package com.example.sharoushi.data.db

import androidx.room.Database
import androidx.room.RoomDatabase
import com.example.sharoushi.data.dao.AnswerHistoryDao
import com.example.sharoushi.data.dao.BookmarkDao
import com.example.sharoushi.data.dao.QuestionDao
import com.example.sharoushi.data.dao.SubjectDao
import com.example.sharoushi.data.entity.AnswerHistoryEntity
import com.example.sharoushi.data.entity.BookmarkEntity
import com.example.sharoushi.data.entity.QuestionEntity
import com.example.sharoushi.data.entity.QuestionFtsEntity
import com.example.sharoushi.data.entity.SubjectEntity

/**
 * Room Database Definition
 */
@Database(
    entities = [
        SubjectEntity::class,
        QuestionEntity::class,
        QuestionFtsEntity::class,
        AnswerHistoryEntity::class,
        BookmarkEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun subjectDao(): SubjectDao
    abstract fun questionDao(): QuestionDao
    abstract fun answerHistoryDao(): AnswerHistoryDao
    abstract fun bookmarkDao(): BookmarkDao
}
