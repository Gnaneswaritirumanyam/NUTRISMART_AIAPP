package com.simats.nutrismartai.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.simats.nutrismartai.data.local.SessionManager
import com.simats.nutrismartai.data.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class AuthState {
    object Idle : AuthState()
    object Loading : AuthState()
    data class Success(val message: String) : AuthState()
    data class Error(val error: String) : AuthState()
}

class AuthViewModel(
    private val repository: AuthRepository,
    private val sessionManager: SessionManager
) : ViewModel() {

    private val _authState = MutableStateFlow<AuthState>(AuthState.Idle)
    val authState: StateFlow<AuthState> = _authState.asStateFlow()
    
    private val _otpEmail = MutableStateFlow("")
    val otpEmail: StateFlow<String> = _otpEmail.asStateFlow()

    fun login(email: String, pass: String) {
        _authState.value = AuthState.Loading
        viewModelScope.launch {
            try {
                val response = repository.login(email, pass)
                sessionManager.saveAuthToken(response.accessToken)
                sessionManager.saveUserName(response.name ?: "User")
                _authState.value = AuthState.Success(response.message)
            } catch (e: Exception) {
                _authState.value = AuthState.Error(e.message ?: "Login failed")
            }
        }
    }

    fun signup(name: String, email: String, pass: String, confirmPass: String) {
        if (pass != confirmPass) {
            _authState.value = AuthState.Error("Passwords do not match")
            return
        }
        _authState.value = AuthState.Loading
        viewModelScope.launch {
            try {
                val response = repository.requestOtp(name, email, pass, confirmPass)
                if (response.success) {
                    _otpEmail.value = email
                    _authState.value = AuthState.Success(response.message)
                } else {
                    _authState.value = AuthState.Error(response.message)
                }
            } catch (e: Exception) {
                _authState.value = AuthState.Error(e.message ?: "Signup failed")
            }
        }
    }

    fun verifyOtp(otp: String) {
        val email = _otpEmail.value
        if (email.isEmpty()) {
            _authState.value = AuthState.Error("Email not found for OTP verification")
            return
        }
        _authState.value = AuthState.Loading
        viewModelScope.launch {
            try {
                val response = repository.verifyOtp(email, otp)
                if (response.success) {
                    // Token is usually set in cookies from the backend. 
                    // Let's assume the user has to login again or backend returns it.
                    // For now, just mark success.
                    _authState.value = AuthState.Success(response.message)
                } else {
                    _authState.value = AuthState.Error(response.message)
                }
            } catch (e: Exception) {
                _authState.value = AuthState.Error(e.message ?: "OTP verification failed")
            }
        }
    }
    
    fun resetState() {
        _authState.value = AuthState.Idle
    }
}

class AuthViewModelFactory(
    private val repository: AuthRepository,
    private val sessionManager: SessionManager
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(AuthViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return AuthViewModel(repository, sessionManager) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
