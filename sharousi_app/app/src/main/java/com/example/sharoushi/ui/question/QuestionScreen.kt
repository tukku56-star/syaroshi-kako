@file:OptIn(ExperimentalMaterial3Api::class)

package com.example.sharoushi.ui.question

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bookmark
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.sharoushi.data.entity.QuestionEntity
import com.example.sharoushi.data.entity.SubjectEntity

@Composable
fun QuestionScreen(
    viewModel: QuestionViewModel = hiltViewModel()
) {
    val isLoading by viewModel.isLoading.collectAsState()
    val loadError by viewModel.loadError.collectAsState()
    val mode by viewModel.mode.collectAsState()
    val subjects by viewModel.subjects.collectAsState()
    val selectedSubjectId by viewModel.selectedSubjectId.collectAsState()
    val selectedDifficulty by viewModel.selectedDifficulty.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    val weakDays by viewModel.weakDays.collectAsState()
    val weakMinErrors by viewModel.weakMinErrors.collectAsState()
    val questions by viewModel.questions.collectAsState()
    val currentIndex by viewModel.currentIndex.collectAsState()
    val currentQuestion by viewModel.currentQuestion.collectAsState()
    val answerResult by viewModel.answerResult.collectAsState()
    val isBookmarked by viewModel.isCurrentQuestionBookmarked.collectAsState()
    val subjectStats by viewModel.subjectStats.collectAsState()
    val dailyStats by viewModel.dailyStats.collectAsState()
    val subjectShortById = subjects.associateBy({ it.id }, { it.shortName })

    val answeredTotal = subjectStats.sumOf { it.total }
    val correctTotal = subjectStats.sumOf { it.correct }
    val accuracy = if (answeredTotal > 0) {
        (correctTotal.toDouble() / answeredTotal.toDouble()) * 100.0
    } else {
        0.0
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    val progressText = if (questions.isNotEmpty()) {
                        "${currentIndex + 1}/${questions.size}"
                    } else {
                        "0/0"
                    }
                    Text("${mode.label}  $progressText")
                },
                actions = {
                    IconButton(
                        onClick = { viewModel.toggleBookmark() },
                        enabled = currentQuestion != null
                    ) {
                        Icon(
                            imageVector = if (isBookmarked) {
                                Icons.Filled.Bookmark
                            } else {
                                Icons.Outlined.BookmarkBorder
                            },
                            contentDescription = "bookmark"
                        )
                    }
                    IconButton(onClick = { viewModel.retryLoad() }) {
                        Icon(Icons.Filled.Refresh, contentDescription = "refresh")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        }
    ) { padding ->
        if (isLoading) {
            Box(
                modifier = Modifier
                    .padding(padding)
                    .fillMaxSize()
            ) {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
            }
            return@Scaffold
        }

        if (loadError != null) {
            Box(
                modifier = Modifier
                    .padding(padding)
                    .fillMaxSize()
            ) {
                Column(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = loadError ?: "読み込みに失敗しました",
                        color = MaterialTheme.colorScheme.error
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Button(onClick = { viewModel.retryLoad() }) {
                        Text("再読み込み")
                    }
                }
            }
            return@Scaffold
        }

        LazyColumn(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                ModeSection(
                    mode = mode,
                    onModeSelected = viewModel::setMode,
                    onRegenerateTest = viewModel::regenerateTestQuestions
                )
            }

            item {
                SubjectSection(
                    subjects = subjects,
                    selectedSubjectId = selectedSubjectId,
                    onSelect = viewModel::setSubject
                )
            }

            item {
                DifficultySection(
                    selectedDifficulty = selectedDifficulty,
                    onSelectDifficulty = viewModel::setDifficulty
                )
            }

            if (mode == StudyMode.SEARCH) {
                item {
                    SearchSection(
                        query = searchQuery,
                        onQueryChange = viewModel::setSearchQuery
                    )
                }
            }

            if (mode == StudyMode.WEAK) {
                item {
                    WeakSection(
                        days = weakDays,
                        minErrors = weakMinErrors,
                        onDaysSelected = viewModel::setWeakDays,
                        onMinErrorsSelected = viewModel::setWeakMinErrors
                    )
                }
            }

            if (currentQuestion == null) {
                item {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Text(
                            text = "条件に一致する問題がありません。",
                            modifier = Modifier.padding(16.dp)
                        )
                    }
                }
            } else {
                item {
                    QuestionCard(
                        question = currentQuestion,
                        subjectLabel = currentQuestion?.let {
                            subjectShortById[it.subjectId] ?: "科目${it.subjectId}"
                        } ?: "",
                        answerResult = answerResult,
                        onAnswer = viewModel::submitAnswer
                    )
                }

                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        OutlinedButton(
                            modifier = Modifier.weight(1f),
                            onClick = { viewModel.goToPreviousQuestion() }
                        ) {
                            Text("← 前へ")
                        }
                        Button(
                            modifier = Modifier.weight(1f),
                            onClick = { viewModel.goToNextQuestion() }
                        ) {
                            Text("次へ →")
                        }
                    }
                }
            }

            item {
                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = "学習統計",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text("解答数: $answeredTotal 問")
                        Text("正答率: ${"%.1f".format(accuracy)}%")
                        Text("学習日数: ${dailyStats.size} 日")
                    }
                }
            }
        }
    }
}

@Composable
private fun ModeSection(
    mode: StudyMode,
    onModeSelected: (StudyMode) -> Unit,
    onRegenerateTest: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            text = "学習モード",
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            StudyMode.entries.forEach { item ->
                FilterChip(
                    selected = mode == item,
                    onClick = { onModeSelected(item) },
                    label = { Text(item.label) }
                )
            }
            if (mode == StudyMode.TEST) {
                AssistChip(
                    onClick = onRegenerateTest,
                    label = { Text("再抽選") },
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Filled.Refresh,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                )
            }
        }
    }
}

@Composable
private fun SubjectSection(
    subjects: List<SubjectEntity>,
    selectedSubjectId: Int?,
    onSelect: (Int?) -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            text = "科目",
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            FilterChip(
                selected = selectedSubjectId == null,
                onClick = { onSelect(null) },
                label = { Text("全科目") }
            )
            subjects.forEach { subject ->
                FilterChip(
                    selected = selectedSubjectId == subject.id,
                    onClick = { onSelect(subject.id) },
                    label = { Text(subject.shortName) }
                )
            }
        }
    }
}

@Composable
private fun DifficultySection(
    selectedDifficulty: String?,
    onSelectDifficulty: (String?) -> Unit
) {
    val levels = listOf("A", "B", "C", "X", "E")
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            text = "難易度",
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            FilterChip(
                selected = selectedDifficulty == null,
                onClick = { onSelectDifficulty(null) },
                label = { Text("すべて") }
            )
            levels.forEach { level ->
                FilterChip(
                    selected = selectedDifficulty == level,
                    onClick = { onSelectDifficulty(level) },
                    label = { Text(level) }
                )
            }
        }
    }
}

@Composable
private fun SearchSection(
    query: String,
    onQueryChange: (String) -> Unit
) {
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        modifier = Modifier.fillMaxWidth(),
        label = { Text("キーワード検索") },
        placeholder = { Text("例: 解雇 休業手当") }
    )
}

@Composable
private fun WeakSection(
    days: Int,
    minErrors: Int,
    onDaysSelected: (Int) -> Unit,
    onMinErrorsSelected: (Int) -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            text = "弱点条件",
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf(7, 30, 90).forEach { option ->
                FilterChip(
                    selected = days == option,
                    onClick = { onDaysSelected(option) },
                    label = { Text("${option}日") }
                )
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf(1, 2, 3).forEach { option ->
                FilterChip(
                    selected = minErrors == option,
                    onClick = { onMinErrorsSelected(option) },
                    label = { Text("${option}回以上") }
                )
            }
        }
    }
}

@Composable
private fun QuestionCard(
    question: QuestionEntity?,
    subjectLabel: String,
    answerResult: AnswerResult?,
    onAnswer: (Boolean) -> Unit
) {
    if (question == null) return

    var statuteExpanded by remember(question.id) { mutableStateOf(false) }
    val result = answerResult

    ElevatedCard(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.elevatedCardElevation(defaultElevation = 3.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "$subjectLabel  ${question.yearJp} 問${question.questionNum} 肢${question.limb}",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.weight(1f))
                AssistChip(
                    onClick = {},
                    enabled = false,
                    label = { Text("難易度 ${question.difficulty}") }
                )
            }

            if (question.accuracyRate != null) {
                Text(
                    text = "正解率: ${"%.1f".format(question.accuracyRate)}%",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.secondary
                )
            }

            Divider()

            Text(
                text = question.bodyText,
                style = MaterialTheme.typography.bodyLarge
            )

            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(
                    modifier = Modifier.weight(1f),
                    onClick = { onAnswer(true) },
                    enabled = result == null
                ) {
                    Text("○")
                }
                OutlinedButton(
                    modifier = Modifier.weight(1f),
                    onClick = { onAnswer(false) },
                    enabled = result == null
                ) {
                    Text("×")
                }
            }

            if (result != null) {
                val resultColor = when (result.isCorrect) {
                    true -> Color(0xFF1B8E3E)
                    false -> MaterialTheme.colorScheme.error
                    null -> MaterialTheme.colorScheme.secondary
                }
                val resultText = when (result.isCorrect) {
                    true -> "正解"
                    false -> "不正解"
                    null -> "正誤不明"
                }
                val expectedText = when (result.expectedAnswer) {
                    true -> "正答: ○"
                    false -> "正答: ×"
                    null -> "正答: 不明"
                }
                Text(
                    text = "$resultText  ($expectedText)",
                    color = resultColor,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
            }

            if (!question.pointText.isNullOrBlank()) {
                SectionBlock(title = "ポイント", body = question.pointText)
            }
            if (!question.explanation.isNullOrBlank()) {
                SectionBlock(title = "解説", body = question.explanation)
            }
            if (!question.legalBasis.isNullOrBlank()) {
                SectionBlock(title = "出題根拠", body = question.legalBasis)
            }
            if (!question.statuteText.isNullOrBlank()) {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(10.dp)) {
                        OutlinedButton(
                            onClick = { statuteExpanded = !statuteExpanded }
                        ) {
                            Text(if (statuteExpanded) "条文を閉じる" else "条文を表示")
                        }
                        if (statuteExpanded) {
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = question.statuteText,
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SectionBlock(
    title: String,
    body: String
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(10.dp)) {
            Text(
                text = title,
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(text = body, style = MaterialTheme.typography.bodySmall)
        }
    }
}
