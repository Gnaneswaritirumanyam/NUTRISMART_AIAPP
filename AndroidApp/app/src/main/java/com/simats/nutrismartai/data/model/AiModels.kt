package com.simats.nutrismartai.data.model

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class AiChatRequest(
    val prompt: String,
    val filters: Map<String, String>? = null
)

@JsonClass(generateAdapter = true)
data class AiChatResponse(
    val text: String
)

@JsonClass(generateAdapter = true)
data class DetectIngredientResponse(
    val ingredients: List<String>,
    @Json(name = "recipe_name") val recipeName: String,
    val steps: List<String>,
    @Json(name = "ocr_text") val ocrText: String
)
