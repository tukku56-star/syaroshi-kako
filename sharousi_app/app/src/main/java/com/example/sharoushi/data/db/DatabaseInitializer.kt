package com.example.sharoushi.data.db

import android.content.Context
import android.util.Log
import androidx.room.withTransaction
import com.example.sharoushi.data.entity.AnswerHistoryEntity
import com.example.sharoushi.data.entity.BookmarkEntity
import com.example.sharoushi.data.entity.QuestionEntity
import com.example.sharoushi.data.entity.SubjectEntity
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.BufferedInputStream
import java.io.FileNotFoundException
import java.io.InputStreamReader
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.zip.GZIPInputStream
import javax.inject.Inject

class DatabaseInitializer @Inject constructor(
    @ApplicationContext
    private val context: Context
) {
    companion object {
        private const val TAG = "DatabaseInitializer"
        private const val PREFS_NAME = "db_initializer"
        private const val KEY_HISTORY_IMPORTED = "history_imported_v1"
        private const val BOOKMARK_HISTORY_ASSET = "付箋出題.md"
        private const val WEAK_HISTORY_ASSET = "弱点出題.md"

        private val HISTORY_HEADER_REGEX = Regex(
            """\*\*(?:付箋|弱点)[\u0020\t\u00A0\u3000]+((?:令和|平成)(?:元|\d+)年)[\u0020\t\u00A0\u3000]+(.+?)[\u0020\t\u00A0\u3000]+問(\d+)[\u0020\t\u00A0\u3000]+肢([A-E])\*\*"""
        )
        private val JAPANESE_YEAR_REGEX = Regex("""(令和|平成)(元|\d+)年""")
    }

    private val prefs by lazy {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    suspend fun importIfNeeded(db: AppDatabase) {
        withContext(Dispatchers.IO) {
            try {
                val existingQuestions = db.questionDao().count()
                if (existingQuestions == 0) {
                    importQuestions(db)
                } else {
                    Log.i(TAG, "Skip question import: question count=$existingQuestions")
                }

                importStudyHistoryIfNeeded(db)
            } catch (e: Exception) {
                Log.e(TAG, "Import failed", e)
                e.printStackTrace()
            }
        }
    }

    private suspend fun importQuestions(db: AppDatabase) {
        val root = readRootJson()
        val subjects = if (root.subjects.isNotEmpty()) {
            root.subjects.map {
                SubjectEntity(
                    id = it.id,
                    name = it.name,
                    shortName = it.shortName,
                    sortOrder = it.sortOrder
                )
            }
        } else {
            root.questions
                .map { it.subjectId }
                .distinct()
                .sorted()
                .mapIndexed { index, subjectId ->
                    SubjectEntity(
                        id = subjectId,
                        name = "科目$subjectId",
                        shortName = "科目$subjectId",
                        sortOrder = index + 1
                    )
                }
        }

        db.withTransaction {
            db.subjectDao().insertAll(subjects)
            db.questionDao().insertAll(root.questions)
            db.questionDao().rebuildFts()
        }
        Log.i(
            TAG,
            "Question import completed: subjects=${subjects.size}, questions=${root.questions.size}"
        )
    }

    private suspend fun importStudyHistoryIfNeeded(db: AppDatabase) {
        if (prefs.getBoolean(KEY_HISTORY_IMPORTED, false)) {
            Log.i(TAG, "Skip history import: already imported")
            return
        }

        val questionCount = db.questionDao().count()
        if (questionCount == 0) {
            Log.i(TAG, "Skip history import: no questions in database")
            return
        }

        val existingBookmarks = db.bookmarkDao().count()
        val existingAnswers = db.answerHistoryDao().count()
        if (existingBookmarks > 0 || existingAnswers > 0) {
            Log.i(
                TAG,
                "Skip history import: existing user data bookmarks=$existingBookmarks answers=$existingAnswers"
            )
            return
        }

        val bookmarkKeys = parseHistoryAsset(BOOKMARK_HISTORY_ASSET)
        val weakKeys = parseHistoryAsset(WEAK_HISTORY_ASSET)
        if (bookmarkKeys.isEmpty() && weakKeys.isEmpty()) {
            Log.i(TAG, "Skip history import: no parseable entries in assets")
            return
        }

        val (bookmarkIds, bookmarkMisses) = resolveQuestionIds(db, bookmarkKeys)
        val (weakIds, weakMisses) = resolveQuestionIds(db, weakKeys)
        val now = currentTimestamp()

        val bookmarks = bookmarkIds.map { questionId ->
            BookmarkEntity(
                questionId = questionId,
                color = 1,
                createdAt = now
            )
        }

        // Use 2 miss records so imported weak items match the default "2回以上" filter.
        val weakHistory = weakIds.flatMap { questionId ->
            listOf(
                AnswerHistoryEntity(
                    questionId = questionId,
                    userAnswer = false,
                    isCorrect = false,
                    answeredAt = now
                ),
                AnswerHistoryEntity(
                    questionId = questionId,
                    userAnswer = false,
                    isCorrect = false,
                    answeredAt = now
                )
            )
        }

        db.withTransaction {
            if (bookmarks.isNotEmpty()) {
                db.bookmarkDao().upsertAll(bookmarks)
            }
            if (weakHistory.isNotEmpty()) {
                db.answerHistoryDao().insertAll(weakHistory)
            }
        }

        prefs.edit().putBoolean(KEY_HISTORY_IMPORTED, true).apply()
        Log.i(
            TAG,
            "History import completed: bookmarks=${bookmarks.size} (missing=$bookmarkMisses), weakQuestions=${weakIds.size} (missing=$weakMisses), answerHistory=${weakHistory.size}"
        )
    }

    private fun parseHistoryAsset(assetName: String): List<HistoryKey> {
        val text = readAssetText(assetName) ?: return emptyList()
        val keys = HISTORY_HEADER_REGEX.findAll(text).mapNotNull { match ->
            val yearJp = match.groupValues[1]
            val subjectLabel = match.groupValues[2]
            val questionNum = match.groupValues[3].toIntOrNull()
            val limb = match.groupValues[4].uppercase(Locale.JAPAN)

            val subjectId = subjectIdFromLabel(subjectLabel)
            val year = toGregorianYear(yearJp)
            if (subjectId == null || year == null || questionNum == null) {
                return@mapNotNull null
            }

            HistoryKey(
                subjectId = subjectId,
                year = year,
                questionNum = questionNum,
                limb = limb
            )
        }.distinct().toList()

        Log.i(TAG, "Parsed history asset: $assetName entries=${keys.size}")
        return keys
    }

    private fun readAssetText(assetName: String): String? {
        return try {
            context.assets.open(assetName).use { input ->
                InputStreamReader(input, Charsets.UTF_8).use { reader ->
                    reader.readText()
                }
            }
        } catch (e: FileNotFoundException) {
            Log.w(TAG, "History asset not found: $assetName")
            null
        }
    }

    private suspend fun resolveQuestionIds(
        db: AppDatabase,
        keys: List<HistoryKey>
    ): Pair<List<Int>, Int> {
        val resolvedIds = LinkedHashSet<Int>()
        var unresolvedCount = 0

        keys.forEach { key ->
            val questionId = db.questionDao().findId(
                subjectId = key.subjectId,
                year = key.year,
                questionNum = key.questionNum,
                limb = key.limb
            )
            if (questionId == null) {
                unresolvedCount += 1
            } else {
                resolvedIds.add(questionId)
            }
        }

        return resolvedIds.toList() to unresolvedCount
    }

    private fun subjectIdFromLabel(rawLabel: String): Int? {
        val label = rawLabel
            .replace('\u00A0', ' ')
            .replace('\u3000', ' ')
            .trim()

        return when {
            label == "労働基準法" -> 1
            label == "労働安全衛生法" -> 2
            label == "労災保険法" -> 3
            label == "雇用保険法" -> 4
            label == "労働保険徴収法" -> 5
            label.startsWith("徴収法") -> 5
            label == "労務管理その他の労働に関する一般常識" -> 6
            label == "一般常識（労一）" -> 6
            label == "健康保険法" -> 7
            label == "厚生年金保険法" -> 8
            label == "国民年金法" -> 9
            label == "社会保険に関する一般常識" -> 10
            label == "一般常識（社一）" -> 10
            else -> null
        }
    }

    private fun toGregorianYear(yearJp: String): Int? {
        val match = JAPANESE_YEAR_REGEX.matchEntire(yearJp.trim()) ?: return null
        val era = match.groupValues[1]
        val rawNum = match.groupValues[2]
        val num = if (rawNum == "元") 1 else rawNum.toIntOrNull() ?: return null
        return when (era) {
            "令和" -> 2018 + num
            "平成" -> 1988 + num
            else -> null
        }
    }

    private fun currentTimestamp(): String {
        val formatter = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.JAPAN)
        return formatter.format(Date())
    }

    private fun readRootJson(): RootJson {
        val candidates = listOf("questions.json.gz", "questions.json")
        var lastError: Exception? = null
        for (name in candidates) {
            try {
                context.assets.open(name).use { input ->
                    BufferedInputStream(input).use { buffered ->
                        buffered.mark(4)
                        val b1 = buffered.read()
                        val b2 = buffered.read()
                        buffered.reset()
                        val isGzip = (b1 == 0x1f && b2 == 0x8b)

                        val reader = if (isGzip) {
                            InputStreamReader(GZIPInputStream(buffered))
                        } else {
                            InputStreamReader(buffered)
                        }

                        reader.use {
                            Log.i(TAG, "Loading question asset: $name (gzip=$isGzip)")
                            return Gson().fromJson(it, RootJson::class.java)
                        }
                    }
                }
            } catch (e: FileNotFoundException) {
                lastError = e
            } catch (e: Exception) {
                lastError = e
                break
            }
        }
        throw (lastError ?: FileNotFoundException("questions.json(.gz) not found in assets"))
    }

    private data class RootJson(
        val subjects: List<SubjectJson> = emptyList(),
        val questions: List<QuestionEntity> = emptyList()
    )

    private data class SubjectJson(
        val id: Int,
        val name: String,
        @SerializedName("short")
        val shortName: String,
        @SerializedName("sort")
        val sortOrder: Int
    )

    private data class HistoryKey(
        val subjectId: Int,
        val year: Int,
        val questionNum: Int,
        val limb: String
    )
}
