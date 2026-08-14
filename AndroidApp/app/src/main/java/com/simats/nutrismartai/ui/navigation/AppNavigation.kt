package com.simats.nutrismartai.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.simats.nutrismartai.data.local.SessionManager
import com.simats.nutrismartai.data.network.RetrofitClient
import com.simats.nutrismartai.data.repository.AuthRepository
import com.simats.nutrismartai.ui.auth.AuthViewModel
import com.simats.nutrismartai.ui.auth.AuthViewModelFactory
import com.simats.nutrismartai.ui.auth.LoginScreen
import com.simats.nutrismartai.ui.auth.OtpScreen
import com.simats.nutrismartai.ui.auth.SignupScreen

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Signup : Screen("signup")
    object Otp : Screen("otp")
    object Dashboard : Screen("dashboard")
}

@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val context = LocalContext.current
    
    val sessionManager = remember { SessionManager(context) }
    val apiService = remember { RetrofitClient.createApiService(sessionManager) }
    val authRepository = remember { AuthRepository(apiService) }

    val authViewModel: AuthViewModel = viewModel(
        factory = AuthViewModelFactory(authRepository, sessionManager)
    )

    NavHost(navController = navController, startDestination = Screen.Login.route) {
        
        composable(Screen.Login.route) {
            LoginScreen(
                viewModel = authViewModel,
                onNavigateToSignup = { navController.navigate(Screen.Signup.route) },
                onLoginSuccess = { 
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                }
            )
        }
        
        composable(Screen.Signup.route) {
            SignupScreen(
                viewModel = authViewModel,
                onNavigateToLogin = { navController.navigate(Screen.Login.route) {
                    popUpTo(Screen.Signup.route) { inclusive = true }
                } },
                onNavigateToOtp = { navController.navigate(Screen.Otp.route) }
            )
        }
        
        composable(Screen.Otp.route) {
            OtpScreen(
                viewModel = authViewModel,
                onVerificationSuccess = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(Screen.Signup.route) { inclusive = true }
                    }
                }
            )
        }
        
        composable(Screen.Dashboard.route) {
            com.simats.nutrismartai.ui.dashboard.DashboardScreen()
        }
    }
}
