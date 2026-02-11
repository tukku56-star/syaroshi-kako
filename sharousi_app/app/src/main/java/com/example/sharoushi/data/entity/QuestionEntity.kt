package com.example.sharoushi.data.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import com.google.gson.annotations.SerializedName

@Entity(
    tableName = "question",
    indices = [
        Index(value = ["subject_id"]),
        Index(value = ["year"]),
        Index(value = ["difficulty"]),
        Index(value = ["is_correct"]),
        Index(
            value = ["subject_id", "year", "question_num", "limb"],
            unique = true
        )
    ]
)
data class QuestionEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,

    @ColumnInfo(name = "subject_id")
    @SerializedName("subject_id")
    val subjectId: Int,

    @ColumnInfo(name = "year")
    @SerializedName("year")
    val year: Int,

    @ColumnInfo(name = "year_jp")
    @SerializedName("year_jp")
    val yearJp: String,

    @ColumnInfo(name = "question_num")
    @SerializedName("question_num")
    val questionNum: Int,

    @ColumnInfo(name = "limb")
    @SerializedName("limb")
    val limb: String,

    @ColumnInfo(name = "difficulty")
    @SerializedName("difficulty")
    val difficulty: String,

    @ColumnInfo(name = "is_correct")
    @SerializedName("is_correct")
    val isCorrect: Boolean?,

    @ColumnInfo(name = "body_text")
    @SerializedName("body")
    val bodyText: String,

    @ColumnInfo(name = "accuracy_rate")
    @SerializedName("accuracy_rate")
    val accuracyRate: Double?,

    @ColumnInfo(name = "point_text")
    @SerializedName("point")
    val pointText: String?,

    @ColumnInfo(name = "explanation")
    @SerializedName("explanation")
    val explanation: String?,

    @ColumnInfo(name = "legal_basis")
    @SerializedName("legal_basis")
    val legalBasis: String?,

    @ColumnInfo(name = "statute_text")
    @SerializedName("statute")
    val statuteText: String?
)
