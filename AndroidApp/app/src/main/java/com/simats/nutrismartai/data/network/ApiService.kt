package com.simats.nutrismartai.data.network

import com.simats.nutrismartai.data.model.AiChatRequest
import com.simats.nutrismartai.data.model.AiChatResponse
import com.simats.nutrismartai.data.model.DetectIngredientResponse
import com.simats.nutrismartai.data.model.LoginRequest
import com.simats.nutrismartai.data.model.LoginResponse
import com.simats.nutrismartai.data.model.SignupRequest
import com.simats.nutrismartai.data.model.SignupResponse
import com.simats.nutrismartai.data.model.VerifyOtpRequest
import com.simats.nutrismartai.data.model.VerifyOtpResponse
import okhttp3.MultipartBody
import retrofit2.http.Body
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface ApiService {
    // Auth endpoints
    @POST("login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @POST("api/auth/signup/request-otp")
    suspend fun requestOtp(@Body request: SignupRequest): SignupResponse

    @POST("api/auth/signup/verify-otp")
    suspend fun verifyOtp(@Body request: VerifyOtpRequest): VerifyOtpResponse
    
    // AI and Scanning
    @POST("api/recipe")
    suspend fun askAi(@Body request: AiChatRequest): AiChatResponse
    
    @Multipart
    @POST("detect")
    suspend fun detectIngredients(@Part file: MultipartBody.Part): DetectIngredientResponse
    
    // Plan endpoints
    // TODO: Add models and routes for generate-health-recipes, get_plans, save_plan, etc.
}
