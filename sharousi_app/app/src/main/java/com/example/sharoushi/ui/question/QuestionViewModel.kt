package com.example.sharoushi.ui.question

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.sharoushi.data.dao.DailyStat
import com.example.sharoushi.data.dao.SubjectStat
import com.example.sharoushi.data.entity.QuestionEntity
import com.example.sharoushi.data.entity.SubjectEntity
import com.example.sharoushi.data.repository.QuestionRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

enum class StudyMode(val label: String) {
    NORMAL("一問一答"),
    BOOKMARK("付箋出題"),
    WEAK("弱点出題"),
    SEARCH("検索"),
    TEST("実践テスト")
}

data class AnswerResult(
    val userAnswer: Boolean,
    val isCorrect: Boolean?,
    val expectedAnswer: Boolean?
)

@HiltViewModel
class QuestionViewModel @Inject constructor(
    private val repository: QuestionRepository
) : ViewModel() {

    private val _isLoading = MutableStateFlow(true)
    val isLoading: StateFlow<Boolean> = _isLoading

    private val _loadError = MutableStateFlow<String?>(null)
    val loadError: StateFlow<String?> = _loadError

    private val _mode = MutableStateFlow(StudyMode.NORMAL)
    val mode: StateFlow<StudyMode> = _mode

    private val _selectedSubjectId = MutableStateFlow<Int?>(null)
    val selectedSubjectId: StateFlow<Int?> = _selectedSubjectId

    private val _selectedYear = MutableStateFlow<Int?>(null)
    val selectedYear: StateFlow<Int?> = _selectedYear

    private val _availableYears = MutableStateFlow<List<Int>>(emptyList())
    val availableYears: StateFlow<List<Int>> = _availableYears

    private val _selectedDifficulty = MutableStateFlow<String?>(null)
    val selectedDifficulty: StateFlow<String?> = _selectedDifficulty

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery

    private val _weakDays = MutableStateFlow(30)
    val weakDays: StateFlow<Int> = _weakDays

    private val _weakMinErrors = MutableStateFlow(2)
    val weakMinErrors: StateFlow<Int> = _weakMinErrors

    private val _subjects = MutableStateFlow<List<SubjectEntity>>(emptyList())
    val subjects: StateFlow<List<SubjectEntity>> = _subjects

    private val _questions = MutableStateFlow<List<QuestionEntity>>(emptyList())
    val questions: StateFlow<List<QuestionEntity>> = _questions

    private val _currentIndex = MutableStateFlow(0)
    val currentIndex: StateFlow<Int> = _currentIndex

    private val _answerResult = MutableStateFlow<AnswerResult?>(null)
    val answerResult: StateFlow<AnswerResult?> = _answerResult

    val currentQuestion: StateFlow<QuestionEntity?> = combine(_questions, _currentIndex) { list, idx ->
        list.getOrNull(idx)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    val bookmarkedQuestionIds: StateFlow<Set<Int>> = repository.observeBookmarkedQuestionIds()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptySet())

    val isCurrentQuestionBookmarked: StateFlow<Boolean> = combine(
        currentQuestion,
        bookmarkedQuestionIds
    ) { question, bookmarkedIds ->
        val id = question?.id ?: return@combine false
        bookmarkedIds.contains(id)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), false)

    val subjectStats: StateFlow<List<SubjectStat>> = repository.getSubjectStats()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val dailyStats: StateFlow<List<DailyStat>> = repository.getDailyStats()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    private var questionsJob: Job? = null
    private var yearsJob: Job? = null

    init {
        initialize()
    }

    fun retryLoad() {
        initialize()
    }

    fun setMode(mode: StudyMode) {
        if (_mode.value == mode) return
        _mode.value = mode
        restartQuestionObserver(resetIndex = true)
    }

    fun setSubject(subjectId: Int?) {
        _selectedSubjectId.value = subjectId
        restartYearObserver()
        restartQuestionObserver(resetIndex = true)
    }

    fun setYear(year: Int?) {
        _selectedYear.value = year
        restartQuestionObserver(resetIndex = true)
    }

    fun setDifficulty(difficulty: String?) {
        _selectedDifficulty.value = difficulty
        restartQuestionObserver(resetIndex = true)
    }

    fun setSearchQuery(query: String) {
        _searchQuery.value = query
        if (_mode.value == StudyMode.SEARCH) {
            restartQuestionObserver(resetIndex = true)
        }
    }

    fun setWeakDays(days: Int) {
        _weakDays.value = days
        if (_mode.value == StudyMode.WEAK) {
            restartQuestionObserver(resetIndex = true)
        }
    }

    fun setWeakMinErrors(minErrors: Int) {
        _weakMinErrors.value = minErrors
        if (_mode.value == StudyMode.WEAK) {
            restartQuestionObserver(resetIndex = true)
        }
    }

    fun regenerateTestQuestions() {
        if (_mode.value != StudyMode.TEST) {
            _mode.value = StudyMode.TEST
        }
        restartQuestionObserver(resetIndex = true)
    }

    fun goToNextQuestion() {
        val size = _questions.value.size
        if (size == 0) return
        val next = (_currentIndex.value + 1).coerceAtMost(size - 1)
        _currentIndex.value = next
        _answerResult.value = null
    }

    fun goToPreviousQuestion() {
        val size = _questions.value.size
        if (size == 0) return
        val prev = (_currentIndex.value - 1).coerceAtLeast(0)
        _currentIndex.value = prev
        _answerResult.value = null
    }

    fun submitAnswer(userAnswer: Boolean) {
        val question = currentQuestion.value ?: return
        viewModelScope.launch {
            val result = repository.submitAnswer(question.id, userAnswer)
            _answerResult.value = AnswerResult(
                userAnswer = userAnswer,
                isCorrect = result,
                expectedAnswer = question.isCorrect
            )
        }
    }

    fun toggleBookmark() {
        val questionId = currentQuestion.value?.id ?: return
        viewModelScope.launch {
            repository.toggleBookmark(questionId)
        }
    }

    private fun initialize() {
        viewModelScope.launch {
            _isLoading.value = true
            _loadError.value = null
            try {
                repository.importDataIfNeeded()
                observeSubjects()
                restartYearObserver()
                restartQuestionObserver(resetIndex = true)
            } catch (e: Exception) {
                _loadError.value = e.message ?: "初期化に失敗しました"
            } finally {
                _isLoading.value = false
            }
        }
    }

    private fun observeSubjects() {
        viewModelScope.launch {
            repository.observeSubjects().collect { list ->
                _subjects.value = list
            }
        }
    }

    private fun restartYearObserver() {
        yearsJob?.cancel()
        yearsJob = viewModelScope.launch {
            repository.observeYears(_selectedSubjectId.value).collect { years ->
                _availableYears.value = years
                if (_selectedYear.value != null && _selectedYear.value !in years) {
                    _selectedYear.value = null
                    restartQuestionObserver(resetIndex = true)
                }
            }
        }
    }

    private fun restartQuestionObserver(resetIndex: Boolean) {
        if (resetIndex) {
            _currentIndex.value = 0
        }
        _answerResult.value = null

        questionsJob?.cancel()
        questionsJob = viewModelScope.launch {
            buildQuestionFlow().collect { list ->
                _questions.value = list
                if (list.isEmpty()) {
                    _currentIndex.value = 0
                } else {
                    _currentIndex.value = _currentIndex.value.coerceIn(0, list.lastIndex)
                }
            }
        }
    }

    private fun buildQuestionFlow(): Flow<List<QuestionEntity>> {
        val year = _selectedYear.value
        val subjectId = _selectedSubjectId.value
        val difficulty = _selectedDifficulty.value

        return when (_mode.value) {
            StudyMode.NORMAL -> repository.getQuestions(
                subjectId = subjectId,
                minYear = year,
                maxYear = year,
                difficulty = difficulty
            )

            StudyMode.BOOKMARK -> repository.getBookmarkedQuestions(
                subjectId = subjectId,
                minYear = year,
                maxYear = year,
                difficulty = difficulty
            )

            StudyMode.WEAK -> repository.getWeakQuestions(
                days = _weakDays.value,
                minErrors = _weakMinErrors.value
            ).map { applyCommonFilters(it) }

            StudyMode.SEARCH -> {
                val query = _searchQuery.value
                if (query.isBlank()) {
                    flowOf(emptyList())
                } else {
                    repository.searchQuestions(query).map { applyCommonFilters(it) }
                }
            }

            StudyMode.TEST -> flow {
                emit(
                    repository.getRandomTestQuestions(
                        subjectId = subjectId,
                        minYear = year,
                        maxYear = year,
                        difficulty = difficulty,
                        limit = 10
                    )
                )
            }
        }
    }

    private fun applyCommonFilters(source: List<QuestionEntity>): List<QuestionEntity> {
        val subjectId = _selectedSubjectId.value
        val year = _selectedYear.value
        val difficulty = _selectedDifficulty.value
        return source.filter { question ->
            (subjectId == null || question.subjectId == subjectId) &&
                (year == null || question.year == year) &&
                (difficulty == null || question.difficulty == difficulty)
        }
    }
}
