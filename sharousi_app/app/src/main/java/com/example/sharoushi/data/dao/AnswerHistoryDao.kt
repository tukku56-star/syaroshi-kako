package com.example.sharoushi.data.dao

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.example.sharoushi.data.entity.AnswerHistoryEntity
import kotlinx.coroutines.flow.Flow

data class SubjectStat(
    @ColumnInfo(name = "subject_id")
    val subjectId: Int,
    val total: Int,
    val correct: Int
)

data class DailyStat(
    val date: String,
    val count: Int
)

@Dao
interface AnswerHistoryDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entry: AnswerHistoryEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(entries: List<AnswerHistoryEntity>)

    @Query("SELECT COUNT(*) FROM answer_history")
    suspend fun count(): Int

    @Query("""
        SELECT q.subject_id,
               COUNT(*) as total,
               SUM(CASE WHEN h.is_correct = 1 THEN 1 ELSE 0 END) as correct
        FROM answer_history h
        INNER JOIN question q ON q.id = h.question_id
        GROUP BY q.subject_id
        ORDER BY q.subject_id ASC
    """)
    fun getSubjectStats(): Flow<List<SubjectStat>>

    @Query("""
        SELECT date(answered_at) as date, COUNT(*) as count
        FROM answer_history
        GROUP BY date(answered_at)
        ORDER BY date DESC
    """)
    fun getDailyStats(): Flow<List<DailyStat>>
}
