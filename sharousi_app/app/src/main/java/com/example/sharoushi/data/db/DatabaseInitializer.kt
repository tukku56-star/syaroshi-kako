package com.example.sharoushi.data.db

import android.content.Context
import androidx.room.withTransaction
import com.example.sharoushi.data.entity.QuestionEntity
import com.example.sharoushi.data.entity.SubjectEntity
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.zip.GZIPInputStream
import javax.inject.Inject

class DatabaseInitializer @Inject constructor(
    @ApplicationContext
    private val context: Context
) {
    suspend fun importIfNeeded(db: AppDatabase) {
        withContext(Dispatchers.IO) {
            if (db.questionDao().count() > 0) {
                return@withContext
            }

            try {
                val root = context.assets.open("questions.json.gz").use { input ->
                    GZIPInputStream(input).bufferedReader().use { reader ->
                        Gson().fromJson(reader, RootJson::class.java)
                    }
                }

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
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
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
