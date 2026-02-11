package com.example.sharoushi.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.example.sharoushi.data.entity.QuestionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface QuestionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(questions: List<QuestionEntity>)

    @Query("SELECT COUNT(*) FROM question")
    suspend fun count(): Int

    @Query("""
        SELECT DISTINCT year
        FROM question
        WHERE (:subjectId IS NULL OR subject_id = :subjectId)
        ORDER BY year DESC
    """)
    fun observeYears(subjectId: Int?): Flow<List<Int>>

    @Query("""
        SELECT * FROM question
        WHERE (:subjectId IS NULL OR subject_id = :subjectId)
        AND (:minYear IS NULL OR year >= :minYear)
        AND (:maxYear IS NULL OR year <= :maxYear)
        AND (:difficulty IS NULL OR difficulty = :difficulty)
        ORDER BY year DESC, question_num ASC, limb ASC
    """)
    fun getQuestions(
        subjectId: Int?,
        minYear: Int?,
        maxYear: Int?,
        difficulty: String?
    ): Flow<List<QuestionEntity>>

    @Query("""
        SELECT * FROM question
        WHERE (:subjectId IS NULL OR subject_id = :subjectId)
        AND (:minYear IS NULL OR year >= :minYear)
        AND (:maxYear IS NULL OR year <= :maxYear)
        AND (:difficulty IS NULL OR difficulty = :difficulty)
        ORDER BY RANDOM()
        LIMIT :limit
    """)
    suspend fun getRandomQuestions(
        subjectId: Int?,
        minYear: Int?,
        maxYear: Int?,
        difficulty: String?,
        limit: Int
    ): List<QuestionEntity>

    @Query("SELECT * FROM question WHERE id = :questionId LIMIT 1")
    suspend fun getById(questionId: Int): QuestionEntity?

    @Query("""
        SELECT id FROM question
        WHERE subject_id = :subjectId
        AND year = :year
        AND question_num = :questionNum
        AND limb = :limb
        LIMIT 1
    """)
    suspend fun findId(
        subjectId: Int,
        year: Int,
        questionNum: Int,
        limb: String
    ): Int?

    @Query("""
        SELECT q.* FROM question q
        INNER JOIN bookmark b ON q.id = b.question_id
        WHERE (:subjectId IS NULL OR q.subject_id = :subjectId)
        AND (:minYear IS NULL OR q.year >= :minYear)
        AND (:maxYear IS NULL OR q.year <= :maxYear)
        AND (:difficulty IS NULL OR q.difficulty = :difficulty)
        ORDER BY b.created_at DESC, q.year DESC, q.question_num ASC, q.limb ASC
    """)
    fun getBookmarkedQuestions(
        subjectId: Int?,
        minYear: Int?,
        maxYear: Int?,
        difficulty: String?
    ): Flow<List<QuestionEntity>>

    @Query("""
        SELECT q.* FROM question q
        INNER JOIN answer_history h ON q.id = h.question_id
        WHERE h.is_correct = 0
        AND h.answered_at >= datetime('now', '-' || :days || ' days')
        GROUP BY q.id
        HAVING COUNT(*) >= :minErrors
        ORDER BY COUNT(*) DESC, MAX(h.answered_at) DESC
    """)
    fun getWeakQuestions(days: Int, minErrors: Int): Flow<List<QuestionEntity>>

    @Query("""
        SELECT q.* FROM question q
        INNER JOIN question_fts f ON f.rowid = q.id
        WHERE question_fts MATCH :query
        ORDER BY q.year DESC, q.question_num ASC, q.limb ASC
    """)
    fun searchQuestions(query: String): Flow<List<QuestionEntity>>

    @Query("INSERT INTO question_fts(question_fts) VALUES('rebuild')")
    suspend fun rebuildFts()
}
