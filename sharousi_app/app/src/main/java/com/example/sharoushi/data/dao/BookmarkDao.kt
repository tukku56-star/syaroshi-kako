package com.example.sharoushi.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.example.sharoushi.data.entity.BookmarkEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface BookmarkDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(bookmark: BookmarkEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(bookmarks: List<BookmarkEntity>)

    @Query("SELECT COUNT(*) FROM bookmark")
    suspend fun count(): Int

    @Query("DELETE FROM bookmark WHERE question_id = :questionId")
    suspend fun deleteByQuestionId(questionId: Int)

    @Query("SELECT EXISTS(SELECT 1 FROM bookmark WHERE question_id = :questionId)")
    suspend fun exists(questionId: Int): Boolean

    @Query("SELECT question_id FROM bookmark")
    fun observeQuestionIds(): Flow<List<Int>>
}
