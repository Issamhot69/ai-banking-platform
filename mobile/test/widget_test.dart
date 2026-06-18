// Basic smoke test: verifies the app boots without throwing.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_banking/main.dart';

void main() {
  testWidgets('App boots without crashing', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: BankingApp()));
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // The app should render a MaterialApp at minimum.
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
