package com.simats.nutrismartai.data.model

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class LoginRequest(
    val email: String,
    val password: String
)

@JsonClass(generateAdapter = true)
data class LoginResponse(
    val message: String,
    val name: String?,
    @Json(name = "access_token") val accessToken: String
)

@JsonClass(generateAdapter = true)
data class SignupRequest(
    val name: String,
    val email: String,
    val password: String,
    val confirmPassword: String,
    val recaptchaToken: String = "android_placeholder_token"
)

@JsonClass(generateAdapter = true)
data class SignupResponse(
    val success: Boolean,
    val message: String,
    val expiresIn: Int?
)

@JsonClass(generateAdapter = true)
data class VerifyOtpRequest(
    val email: String,
    val otp: String
)

@JsonClass(generateAdapter = true)
data class VerifyOtpResponse(
    val success: Boolean,
    val message: String,
    val name: String?
)
