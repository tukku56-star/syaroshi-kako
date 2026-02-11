package com.example.sharoushi.data.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "answer_history",
    foreignKeys = [
        ForeignKey(
            entity = QuestionEntity::class,
            parentColumns = ["id"],
            childColumns = ["question_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index(value = ["question_id"])]
)
data class AnswerHistoryEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,

    @ColumnInfo(name = "question_id")
    val questionId: Int,

    @ColumnInfo(name = "user_answer")
    val userAnswer: Boolean,

    @ColumnInfo(name = "is_correct")
    val isCorrect: Boolean,

    @ColumnInfo(
        name = "answered_at",
        defaultValue = "(datetime('now','localtime'))"
    )
    val answeredAt: String? = null
)
