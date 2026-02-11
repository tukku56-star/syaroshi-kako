package com.example.sharoushi.data.repository

import com.example.sharoushi.data.dao.AnswerHistoryDao
import com.example.sharoushi.data.dao.BookmarkDao
import com.example.sharoushi.data.dao.DailyStat
import com.example.sharoushi.data.dao.QuestionDao
import com.example.sharoushi.data.dao.SubjectDao
import com.example.sharoushi.data.dao.SubjectStat
import com.example.sharoushi.data.entity.AnswerHistoryEntity
import com.example.sharoushi.data.entity.BookmarkEntity
import com.example.sharoushi.data.entity.SubjectEntity
import com.example.sharoushi.data.db.AppDatabase
import com.example.sharoushi.data.db.DatabaseInitializer
import com.example.sharoushi.data.entity.QuestionEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class QuestionRepository @Inject constructor(
    private val db: AppDatabase,
    private val questionDao: QuestionDao,
    private val subjectDao: SubjectDao,
    private val answerHistoryDao: AnswerHistoryDao,
    private val bookmarkDao: BookmarkDao,
    private val databaseInitializer: DatabaseInitializer,
) {
    suspend fun importDataIfNeeded() {
        databaseInitializer.importIfNeeded(db)
    }

    fun observeSubjects(): Flow<List<SubjectEntity>> {
        return subjectDao.observeAll()
    }

    fun observeYears(subjectId: Int?): Flow<List<Int>> {
        return questionDao.observeYears(subjectId)
    }

    fun getQuestions(
        subjectId: Int? = null,
        minYear: Int? = null,
        maxYear: Int? = null,
        difficulty: String? = null
    ): Flow<List<QuestionEntity>> {
        return questionDao.getQuestions(subjectId, minYear, maxYear, difficulty)
    }

    fun getWeakQuestions(days: Int, minErrors: Int): Flow<List<QuestionEntity>> {
        return questionDao.getWeakQuestions(days, minErrors)
    }

    fun getBookmarkedQuestions(
        subjectId: Int? = null,
        minYear: Int? = null,
        maxYear: Int? = null,
        difficulty: String? = null
    ): Flow<List<QuestionEntity>> {
        return questionDao.getBookmarkedQuestions(subjectId, minYear, maxYear, difficulty)
    }

    fun searchQuestions(rawQuery: String): Flow<List<QuestionEntity>> {
        val ftsQuery = buildFtsQuery(rawQuery) ?: return flowOf(emptyList())
        return questionDao.searchQuestions(ftsQuery)
    }

    suspend fun getRandomTestQuestions(
        subjectId: Int?,
        minYear: Int?,
        maxYear: Int?,
        difficulty: String?,
        limit: Int = 10
    ): List<QuestionEntity> {
        return questionDao.getRandomQuestions(
            subjectId = subjectId,
            minYear = minYear,
            maxYear = maxYear,
            difficulty = difficulty,
            limit = limit
        )
    }

    suspend fun submitAnswer(questionId: Int, userAnswer: Boolean): Boolean? {
        val question = questionDao.getById(questionId) ?: return null
        val expected = question.isCorrect ?: return null
        val isCorrect = (expected == userAnswer)

        answerHistoryDao.insert(
            AnswerHistoryEntity(
                questionId = questionId,
                userAnswer = userAnswer,
                isCorrect = isCorrect
            )
        )
        return isCorrect
    }

    fun observeBookmarkedQuestionIds(): Flow<Set<Int>> {
        return bookmarkDao.observeQuestionIds().map { it.toSet() }
    }

    suspend fun toggleBookmark(questionId: Int, color: Int = 1) {
        if (bookmarkDao.exists(questionId)) {
            bookmarkDao.deleteByQuestionId(questionId)
        } else {
            bookmarkDao.upsert(BookmarkEntity(questionId = questionId, color = color))
        }
    }

    fun getSubjectStats(): Flow<List<SubjectStat>> {
        return answerHistoryDao.getSubjectStats()
    }

    fun getDailyStats(): Flow<List<DailyStat>> {
        return answerHistoryDao.getDailyStats()
    }

    suspend fun getQuestionCount(): Int {
        return questionDao.count()
    }

    private fun buildFtsQuery(raw: String): String? {
        val cleaned = raw
            .replace(Regex("""["'():]"""), " ")
            .trim()
        if (cleaned.isBlank()) return null

        val tokens = cleaned
            .split(Regex("""\s+"""))
            .map { it.trim() }
            .filter { it.isNotBlank() }

        if (tokens.isEmpty()) return null
        return tokens.joinToString(" AND ") { "\"$it\"*" }
    }
}
