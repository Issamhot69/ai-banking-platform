import 'package:flutter/material.dart';

class AppColors {
  static const Color primary = Color(0xFF6C63FF);
  static const Color primaryDark = Color(0xFF5A52D5);
  static const Color primaryLight = Color(0xFF8B85FF);
  static const Color background = Color(0xFF0A0E1A);
  static const Color surface = Color(0xFF141828);
  static const Color surfaceLight = Color(0xFF1E2340);
  static const Color card = Color(0xFF1A1F35);
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xFF8B92A5);
  static const Color textHint = Color(0xFF4A5068);
  static const Color success = Color(0xFF00D4AA);
  static const Color error = Color(0xFFFF4757);
  static const Color warning = Color(0xFFFFB347);
  static const Color info = Color(0xFF4ECDC4);
  static const List<Color> primaryGradient = [Color(0xFF6C63FF), Color(0xFF9B59B6)];
  static const List<Color> goldGradient = [Color(0xFFFFD700), Color(0xFFFFA500)];
  static const List<Color> greenGradient = [Color(0xFF00D4AA), Color(0xFF00B894)];
  static const List<Color> redGradient = [Color(0xFFFF4757), Color(0xFFFF3742)];
}

class AppTheme {
  static ThemeData get darkTheme => ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    fontFamily: 'Poppins',
    colorScheme: const ColorScheme.dark(
      primary: AppColors.primary,
      secondary: AppColors.success,
      surface: AppColors.surface,
      background: AppColors.background,
      error: AppColors.error,
    ),
    scaffoldBackgroundColor: AppColors.background,
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.background,
      elevation: 0,
      titleTextStyle: TextStyle(color: AppColors.textPrimary, fontSize: 20, fontWeight: FontWeight.w600, fontFamily: 'Poppins'),
      iconTheme: IconThemeData(color: AppColors.textPrimary),
    ),
    cardTheme: CardThemeData(color: AppColors.card, elevation: 0, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        minimumSize: const Size(double.infinity, 56),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, fontFamily: 'Poppins'),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surfaceLight,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppColors.surfaceLight)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppColors.primary, width: 2)),
      labelStyle: const TextStyle(color: AppColors.textSecondary),
      hintStyle: const TextStyle(color: AppColors.textHint),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: AppColors.surface,
      selectedItemColor: AppColors.primary,
      unselectedItemColor: AppColors.textHint,
      type: BottomNavigationBarType.fixed,
      elevation: 0,
    ),
  );
}
