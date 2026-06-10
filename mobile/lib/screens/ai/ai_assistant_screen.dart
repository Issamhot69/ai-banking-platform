import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../config/app_theme.dart';
import '../../services/api_service.dart';

class AIAssistantScreen extends ConsumerStatefulWidget {
  const AIAssistantScreen({super.key});
  @override
  ConsumerState<AIAssistantScreen> createState() => _AIAssistantScreenState();
}

class _AIAssistantScreenState extends ConsumerState<AIAssistantScreen> {
  final _messageCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final List<ChatMessage> _messages = [];
  List<Map<String, dynamic>> _history = [];
  bool _isTyping = false;

  @override
  void initState() { super.initState(); _addWelcome(); }

  void _addWelcome() {
    _messages.add(ChatMessage(
      text: '👋 Bonjour ! Je suis votre assistant bancaire IA.\n\nJe peux vous aider avec :\n• 💰 Vos soldes et transactions\n• 💸 Virements et paiements\n• 📊 Analyse de vos dépenses\n• 💳 Gestion de vos cartes\n• 🎯 Conseils financiers personnalisés',
      isUser: false, time: DateTime.now(),
    ));
  }

  Future<void> _send() async {
    final text = _messageCtrl.text.trim();
    if (text.isEmpty) return;
    _messageCtrl.clear();
    setState(() { _messages.add(ChatMessage(text: text, isUser: true, time: DateTime.now())); _isTyping = true; });
    _scrollToBottom();
    try {
      final response = await apiService.chat(text, history: _history);
      final reply = response['reply'] as String;
      _history.add({'role': 'user', 'content': text});
      _history.add({'role': 'assistant', 'content': reply});
      if (_history.length > 20) _history = _history.sublist(_history.length - 20);
      setState(() { _isTyping = false; _messages.add(ChatMessage(text: reply, isUser: false, time: DateTime.now())); });
    } catch (e) {
      setState(() { _isTyping = false; _messages.add(ChatMessage(text: 'Désolé, une erreur est survenue.', isUser: false, time: DateTime.now(), isError: true)); });
    }
    _scrollToBottom();
  }

  void _scrollToBottom() => Future.delayed(const Duration(milliseconds: 100), () {
    if (_scrollCtrl.hasClients) _scrollCtrl.animateTo(_scrollCtrl.position.maxScrollExtent, duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
  });

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: Row(children: [
        Container(width: 40, height: 40, decoration: BoxDecoration(gradient: const LinearGradient(colors: AppColors.primaryGradient), borderRadius: BorderRadius.circular(12)), child: const Icon(Icons.smart_toy_rounded, color: Colors.white, size: 22)),
        const SizedBox(width: 12),
        const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('AI Assistant', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          Text('Powered by Claude', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
        ]),
      ]),
      actions: [IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: () => setState(() { _messages.clear(); _history.clear(); _addWelcome(); }))],
    ),
    body: Column(children: [
      _buildQuickActions(),
      Expanded(child: ListView.builder(
        controller: _scrollCtrl, padding: const EdgeInsets.all(16),
        itemCount: _messages.length + (_isTyping ? 1 : 0),
        itemBuilder: (_, i) => i == _messages.length ? _buildTyping() : _buildBubble(_messages[i]),
      )),
      _buildInput(),
    ]),
  );

  Widget _buildQuickActions() => SizedBox(
    height: 44,
    child: ListView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6), children: [
      '💰 Mon solde', '📊 Analyse dépenses', '💡 Conseils épargne', '🎯 Credit score',
    ].map((q) => GestureDetector(
      onTap: () { _messageCtrl.text = q.replaceAll(RegExp(r'[^\w\s]'), '').trim(); _send(); },
      child: Container(margin: const EdgeInsets.only(right: 8), padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6), decoration: BoxDecoration(color: AppColors.surfaceLight, borderRadius: BorderRadius.circular(20), border: Border.all(color: AppColors.primary.withOpacity(0.3))), child: Text(q, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary))),
    )).toList()),
  );

  Widget _buildBubble(ChatMessage msg) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Row(mainAxisAlignment: msg.isUser ? MainAxisAlignment.end : MainAxisAlignment.start, crossAxisAlignment: CrossAxisAlignment.end, children: [
      if (!msg.isUser) ...[Container(width: 32, height: 32, decoration: BoxDecoration(gradient: const LinearGradient(colors: AppColors.primaryGradient), borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.smart_toy_rounded, color: Colors.white, size: 16)), const SizedBox(width: 8)],
      Flexible(child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: msg.isUser ? AppColors.primary : msg.isError ? AppColors.error.withOpacity(0.2) : AppColors.card,
          borderRadius: BorderRadius.circular(20).copyWith(bottomRight: msg.isUser ? const Radius.circular(4) : null, bottomLeft: !msg.isUser ? const Radius.circular(4) : null),
        ),
        child: Text(msg.text, style: TextStyle(color: msg.isError ? AppColors.error : AppColors.textPrimary, fontSize: 14, height: 1.5)),
      )),
      if (msg.isUser) const SizedBox(width: 8),
    ]),
  );

  Widget _buildTyping() => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Row(children: [
      Container(width: 32, height: 32, decoration: BoxDecoration(gradient: const LinearGradient(colors: AppColors.primaryGradient), borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.smart_toy_rounded, color: Colors.white, size: 16)),
      const SizedBox(width: 8),
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(20).copyWith(bottomLeft: const Radius.circular(4))),
        child: Row(children: List.generate(3, (i) => Container(width: 8, height: 8, margin: const EdgeInsets.symmetric(horizontal: 2), decoration: BoxDecoration(color: AppColors.primary.withOpacity(0.5 + i * 0.25), shape: BoxShape.circle)))),
      ),
    ]),
  );

  Widget _buildInput() => Container(
    padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
    decoration: const BoxDecoration(color: AppColors.surface, border: Border(top: BorderSide(color: AppColors.surfaceLight))),
    child: SafeArea(child: Row(children: [
      Expanded(child: TextField(
        controller: _messageCtrl, style: const TextStyle(color: AppColors.textPrimary), maxLines: null,
        decoration: InputDecoration(hintText: 'Posez votre question...', hintStyle: const TextStyle(color: AppColors.textHint), filled: true, fillColor: AppColors.surfaceLight, border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none), contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12)),
        onSubmitted: (_) => _send(),
      )),
      const SizedBox(width: 8),
      GestureDetector(
        onTap: _isTyping ? null : _send,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          width: 48, height: 48,
          decoration: BoxDecoration(gradient: LinearGradient(colors: _isTyping ? [AppColors.textHint, AppColors.textHint] : AppColors.primaryGradient), borderRadius: BorderRadius.circular(16)),
          child: Icon(_isTyping ? Icons.hourglass_empty : Icons.send_rounded, color: Colors.white, size: 20),
        ),
      ),
    ])),
  );
}

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime time;
  final bool isError;
  ChatMessage({required this.text, required this.isUser, required this.time, this.isError = false});
}
