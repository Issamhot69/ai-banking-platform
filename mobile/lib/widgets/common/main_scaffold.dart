import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../config/app_theme.dart';

class MainScaffold extends StatelessWidget {
  final Widget child;
  const MainScaffold({super.key, required this.child});

  static int getIndex(BuildContext context) {
    final location = GoRouterState.of(context).uri.toString();
    if (location.startsWith('/home')) return 0;
    if (location.startsWith('/accounts')) return 1;
    if (location.startsWith('/transactions') || location.startsWith('/transfer')) return 2;
    if (location.startsWith('/cards')) return 3;
    if (location.startsWith('/ai')) return 4;
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final currentIndex = getIndex(context);
    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(color: AppColors.surface, boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 20, offset: const Offset(0, -5))]),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _NavItem(icon: Icons.home_rounded, label: 'Home', isSelected: currentIndex == 0, route: '/home'),
                _NavItem(icon: Icons.account_balance_wallet_rounded, label: 'Comptes', isSelected: currentIndex == 1, route: '/accounts'),
                _NavItem(icon: Icons.swap_horiz_rounded, label: 'Virement', isSelected: currentIndex == 2, route: '/transfer', isCenter: true),
                _NavItem(icon: Icons.credit_card_rounded, label: 'Cartes', isSelected: currentIndex == 3, route: '/cards'),
                _NavItem(icon: Icons.smart_toy_rounded, label: 'AI', isSelected: currentIndex == 4, route: '/ai'),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final String route;
  final bool isCenter;

  const _NavItem({required this.icon, required this.label, required this.isSelected, required this.route, this.isCenter = false});

  @override
  Widget build(BuildContext context) {
    if (isCenter) {
      return GestureDetector(
        onTap: () => context.go(route),
        child: Container(
          width: 56, height: 56,
          decoration: BoxDecoration(
            gradient: const LinearGradient(colors: AppColors.primaryGradient, begin: Alignment.topLeft, end: Alignment.bottomRight),
            borderRadius: BorderRadius.circular(16),
            boxShadow: [BoxShadow(color: AppColors.primary.withOpacity(0.4), blurRadius: 12, offset: const Offset(0, 4))],
          ),
          child: Icon(icon, color: Colors.white, size: 24),
        ),
      );
    }
    return GestureDetector(
      onTap: () => context.go(route),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary.withOpacity(0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon, color: isSelected ? AppColors.primary : AppColors.textHint, size: 24),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(fontSize: 10, color: isSelected ? AppColors.primary : AppColors.textHint, fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal)),
        ]),
      ),
    );
  }
}
