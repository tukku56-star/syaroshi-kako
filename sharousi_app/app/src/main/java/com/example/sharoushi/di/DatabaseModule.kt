package com.example.sharoushi.di

import android.content.Context
import androidx.room.Room
import com.example.sharoushi.data.dao.AnswerHistoryDao
import com.example.sharoushi.data.dao.BookmarkDao
import com.example.sharoushi.data.dao.QuestionDao
import com.example.sharoushi.data.dao.SubjectDao
import com.example.sharoushi.data.db.AppDatabase
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(
        @ApplicationContext context: Context
    ): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "sharoushi_db"
        )
        .fallbackToDestructiveMigration()
        .build()
    }

    @Provides
    @Singleton
    fun provideQuestionDao(db: AppDatabase): QuestionDao {
        return db.questionDao()
    }

    @Provides
    @Singleton
    fun provideSubjectDao(db: AppDatabase): SubjectDao {
        return db.subjectDao()
    }

    @Provides
    @Singleton
    fun provideAnswerHistoryDao(db: AppDatabase): AnswerHistoryDao {
        return db.answerHistoryDao()
    }

    @Provides
    @Singleton
    fun provideBookmarkDao(db: AppDatabase): BookmarkDao {
        return db.bookmarkDao()
    }
}
