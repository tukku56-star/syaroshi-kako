package com.example.sharoushi.data.db

import android.content.Context
import android.util.Log
import androidx.room.withTransaction
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
import java.util.zip.GZIPInputStream
import javax.inject.Inject

class DatabaseInitializer @Inject constructor(
    @ApplicationContext
    private val context: Context
) {
    companion object {
        private const val TAG = "DatabaseInitializer"
    }

    suspend fun importIfNeeded(db: AppDatabase) {
        withContext(Dispatchers.IO) {
            val existing = db.questionDao().count()
            if (existing > 0) {
                Log.i(TAG, "Skip import: question count=$existing")
                return@withContext
            }

            try {
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
                    "Import completed: subjects=${subjects.size}, questions=${root.questions.size}"
                )
            } catch (e: Exception) {
                Log.e(TAG, "Import failed", e)
                e.printStackTrace()
            }
        }
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
}
