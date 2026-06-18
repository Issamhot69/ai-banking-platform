import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../screens/auth/splash_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/other_screens.dart';
import '../screens/home/home_screen.dart';
import '../screens/ai/ai_assistant_screen.dart';
import '../widgets/common/main_scaffold.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/splash',
    routes: [
      GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),
      GoRoute(path: '/biometric', builder: (_, __) => const BiometricScreen()),
      ShellRoute(
        builder: (context, state, child) => MainScaffold(child: child),
        routes: [
          GoRoute(path: '/home', builder: (_, __) => const HomeScreen()),
          GoRoute(path: '/accounts', builder: (_, __) => const AccountsScreen()),
          GoRoute(path: '/transactions/:accountId', builder: (_, state) => TransactionsScreen(accountId: state.pathParameters['accountId']!)),
          GoRoute(path: '/transfer', builder: (_, __) => const TransferScreen()),
          GoRoute(path: '/cards', builder: (_, __) => const CardsScreen()),
          GoRoute(path: '/ai', builder: (_, __) => const AIAssistantScreen()),
          GoRoute(path: '/analytics', builder: (_, __) => const AnalyticsScreen()),
          GoRoute(path: '/notifications', builder: (_, __) => const NotificationsScreen()),
        ],
      ),
    ],
  );
});
