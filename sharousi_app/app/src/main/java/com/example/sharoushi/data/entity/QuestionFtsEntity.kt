package com.example.sharoushi.data.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Fts4

@Fts4(contentEntity = QuestionEntity::class)
@Entity(tableName = "question_fts")
data class QuestionFtsEntity(
    @ColumnInfo(name = "body_text")
    val bodyText: String,

    val explanation: String?,

    @ColumnInfo(name = "statute_text")
    val statuteText: String?
)
