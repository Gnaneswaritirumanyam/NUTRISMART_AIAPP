package com.simats.nutrismartai.data.repository

import com.simats.nutrismartai.data.model.LoginRequest
import com.simats.nutrismartai.data.model.SignupRequest
import com.simats.nutrismartai.data.model.VerifyOtpRequest
import com.simats.nutrismartai.data.network.ApiService

class AuthRepository(private val apiService: ApiService) {
    
    suspend fun login(email: String, password: String) = 
        apiService.login(LoginRequest(email, password))
        
    suspend fun requestOtp(name: String, email: String, pass: String, confirmPass: String) =
        apiService.requestOtp(SignupRequest(name, email, pass, confirmPass))
        
    suspend fun verifyOtp(email: String, otp: String) =
        apiService.verifyOtp(VerifyOtpRequest(email, otp))
}
