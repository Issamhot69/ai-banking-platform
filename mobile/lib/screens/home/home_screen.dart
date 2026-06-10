import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../config/app_theme.dart';
import '../../services/api_service.dart';
import '../../models/models.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});
  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  User? _user;
  Map<String, dynamic>? _accountsData;
  bool _isLoading = true;
  bool _balanceVisible = true;

  @override
  void initState() { super.initState(); _loadData(); }

  Future<void> _loadData() async {
    try {
      final user = await apiService.getMe();
      final accounts = await apiService.getAccounts();
      setState(() { _user = user; _accountsData = accounts; _isLoading = false; });
    } catch (_) { setState(() => _isLoading = false); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
          : RefreshIndicator(
              onRefresh: _loadData, color: AppColors.primary,
              child: SingleChildScrollView(physics: const AlwaysScrollableScrollPhysics(), child: Column(children: [
                _buildHeader(), _buildBalanceCard(), _buildQuickActions(), _buildRecentTransactions(), _buildAIInsights(),
              ])),
            ),
    ),
  );

  Widget _buildHeader() => Padding(
    padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
    child: Row(children: [
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Bonjour, ${_user?.firstName ?? 'Utilisateur'} 👋', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        const Text('Bienvenue sur AI Banking', style: TextStyle(color: AppColors.textSecondary, fontSize: 14)),
      ]),
      const Spacer(),
      Stack(children: [
        IconButton(onPressed: () => context.go('/notifications'), icon: const Icon(Icons.notifications_outlined)),
        Positioned(right: 8, top: 8, child: Container(width: 8, height: 8, decoration: const BoxDecoration(color: AppColors.error, shape: BoxShape.circle))),
      ]),
      CircleAvatar(radius: 20, backgroundColor: AppColors.primary, child: Text(_user?.firstName.substring(0, 1).toUpperCase() ?? 'U', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold))),
    ]),
  );

  Widget _buildBalanceCard() {
    final total = _accountsData?['total_balance'] ?? 0.0;
    final count = _accountsData?['total_accounts'] ?? 0;
    return Container(
      margin: const EdgeInsets.all(24),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: AppColors.primaryGradient, begin: Alignment.topLeft, end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [BoxShadow(color: AppColors.primary.withOpacity(0.3), blurRadius: 20, offset: const Offset(0, 10))],
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Text('Solde total', style: TextStyle(color: Colors.white70, fontSize: 14)),
          const Spacer(),
          GestureDetector(onTap: () => setState(() => _balanceVisible = !_balanceVisible), child: Icon(_balanceVisible ? Icons.visibility : Icons.visibility_off, color: Colors.white70, size: 20)),
        ]),
        const SizedBox(height: 8),
        Text(_balanceVisible ? NumberFormat.currency(symbol: '€').format(double.parse(total.toString())) : '••••••', style: const TextStyle(color: Colors.white, fontSize: 36, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        Row(children: [
          const Icon(Icons.trending_up, color: Colors.white70, size: 16), const SizedBox(width: 4),
          const Text('+2.4%', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
          const SizedBox(width: 24),
          const Icon(Icons.account_balance_wallet, color: Colors.white70, size: 16), const SizedBox(width: 4),
          Text('$count comptes', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
        ]),
      ]),
    );
  }

  Widget _buildQuickActions() => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 24),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Actions rapides', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      const SizedBox(height: 16),
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        _buildAction(Icons.send_rounded, 'Envoyer', '/transfer', AppColors.primary),
        _buildAction(Icons.download_rounded, 'Recevoir', '/accounts', AppColors.success),
        _buildAction(Icons.credit_card_rounded, 'Cartes', '/cards', AppColors.warning),
        _buildAction(Icons.bar_chart_rounded, 'Stats', '/analytics', AppColors.info),
      ]),
    ]),
  );

  Widget _buildAction(IconData icon, String label, String route, Color color) => GestureDetector(
    onTap: () => context.go(route),
    child: Column(children: [
      Container(width: 60, height: 60, decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(16), border: Border.all(color: color.withOpacity(0.2))), child: Icon(icon, color: color, size: 26)),
      const SizedBox(height: 8),
      Text(label, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
    ]),
  );

  Widget _buildRecentTransactions() => Padding(
    padding: const EdgeInsets.all(24),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        const Text('Transactions récentes', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const Spacer(),
        GestureDetector(onTap: () => context.go('/transactions'), child: const Text('Voir tout', style: TextStyle(color: AppColors.primary, fontSize: 14))),
      ]),
      const SizedBox(height: 16),
      _buildTx('Starbucks', '-€4.50', Icons.coffee, AppColors.warning, '14:25'),
      _buildTx('Salaire reçu', '+€2,500.00', Icons.work, AppColors.success, '09:00'),
      _buildTx('Netflix', '-€13.99', Icons.play_circle, AppColors.error, 'Hier'),
      _buildTx('Uber', '-€18.40', Icons.directions_car, AppColors.info, 'Hier'),
    ]),
  );

  Widget _buildTx(String title, String amount, IconData icon, Color color, String time) => Container(
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(16)),
    child: Row(children: [
      Container(width: 48, height: 48, decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)), child: Icon(icon, color: color, size: 22)),
      const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontWeight: FontWeight.w600)), Text(time, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12))])),
      Text(amount, style: TextStyle(fontWeight: FontWeight.bold, color: amount.startsWith('+') ? AppColors.success : AppColors.textPrimary, fontSize: 16)),
    ]),
  );

  Widget _buildAIInsights() => Container(
    margin: const EdgeInsets.fromLTRB(24, 0, 24, 24),
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      gradient: LinearGradient(colors: [AppColors.success.withOpacity(0.15), AppColors.info.withOpacity(0.15)]),
      borderRadius: BorderRadius.circular(20),
      border: Border.all(color: AppColors.success.withOpacity(0.3)),
    ),
    child: Row(children: [
      Container(width: 48, height: 48, decoration: BoxDecoration(color: AppColors.success.withOpacity(0.2), borderRadius: BorderRadius.circular(12)), child: const Icon(Icons.smart_toy_rounded, color: AppColors.success)),
      const SizedBox(width: 12),
      const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('💡 Conseil IA du jour', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        SizedBox(height: 4),
        Text('Vous économisez 15% de plus ce mois !', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
      ])),
      IconButton(onPressed: () => context.go('/ai'), icon: const Icon(Icons.arrow_forward_ios, color: AppColors.success, size: 16)),
    ]),
  );
}
