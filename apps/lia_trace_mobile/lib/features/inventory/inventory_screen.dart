import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../../core/theme/app_colors.dart';
import '../scanner/sku_scanner_screen.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  final TextEditingController _searchController = TextEditingController();

  final FocusNode _searchFocus = FocusNode();

  static const String _apiUrl = 'http://192.168.1.65:8000/api/v1/inventory';

  String _searchText = '';
  Map<String, dynamic>? _product;
  String? _message;
  bool _isLoading = false;
  int _searchVersion = 0;

  @override
  void dispose() {
    _searchController.dispose();
    _searchFocus.dispose();
    super.dispose();
  }

  void _selectAllText() {
    final text = _searchController.text;

    _searchController.selection = TextSelection(
      baseOffset: 0,
      extentOffset: text.length,
    );
  }

  Future<void> _searchProduct() async {
    FocusScope.of(context).unfocus();

    final sku = _searchController.text.trim();
    final version = ++_searchVersion;

    setState(() {
      _searchText = sku;
      _product = null;
      _message = null;
      _isLoading = sku.isNotEmpty;
    });

    if (sku.isEmpty) {
      setState(() {
        _message = 'Escribe o escanea un SKU.';
      });
      return;
    }

    try {
      debugPrint('LIA TRACE: buscando SKU [$sku]');

      final response = await http
          .get(Uri.parse(_apiUrl))
          .timeout(const Duration(seconds: 15));

      debugPrint('LIA TRACE: respuesta HTTP ${response.statusCode}');

      if (response.statusCode != 200) {
        throw Exception('FastAPI respondió HTTP ${response.statusCode}');
      }

      final decoded = jsonDecode(response.body);

      if (decoded is! List) {
        throw const FormatException(
          'La respuesta del inventario no es una lista.',
        );
      }

      Map<String, dynamic>? foundProduct;

      for (final item in decoded) {
        if (item is Map<String, dynamic>) {
          final itemSku = item['sku']?.toString().trim() ?? '';

          if (itemSku.toLowerCase() == sku.toLowerCase()) {
            foundProduct = item;
            break;
          }
        }
      }

      if (!mounted || version != _searchVersion) {
        return;
      }

      setState(() {
        _product = foundProduct;
        _isLoading = false;
        _message = foundProduct == null ? 'Producto no encontrado: $sku' : null;
      });
    } catch (error) {
      debugPrint('LIA TRACE ERROR HTTP: $error');

      if (!mounted || version != _searchVersion) {
        return;
      }

      setState(() {
        _isLoading = false;
        _message = 'Error al consultar FastAPI:\n$error';
      });
    }
  }

  Future<void> _scanSku() async {
    FocusScope.of(context).unfocus();

    final scannedSku = await Navigator.of(context).push<String>(
      MaterialPageRoute<String>(builder: (context) => const SkuScannerScreen()),
    );

    if (!mounted || scannedSku == null || scannedSku.trim().isEmpty) {
      return;
    }

    final sku = scannedSku.trim();

    // Invalidar consultas anteriores.
    _searchVersion++;

    _searchController.text = sku;
    _selectAllText();

    setState(() {
      _searchText = sku;
      _product = null;
      _message = null;
      _isLoading = false;
    });

    // Permitir que termine la transición desde la cámara.
    await Future<void>.delayed(const Duration(milliseconds: 500));

    if (!mounted || _searchController.text.trim() != sku) {
      return;
    }

    await _searchProduct();
  }

  void _clearSearch() {
    _searchVersion++;
    _searchController.clear();

    setState(() {
      _searchText = '';
      _product = null;
      _message = null;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Inventario',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const Text(
              'Control de existencias',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            const Text(
              'Consulta de materiales en LIA TRACE',
              style: TextStyle(color: AppColors.textSecondary),
            ),

            const SizedBox(height: 24),

            TextField(
              controller: _searchController,
              focusNode: _searchFocus,
              onTap: _selectAllText,
              onChanged: (value) {
                _searchVersion++;

                setState(() {
                  _searchText = value.trim();
                  _product = null;
                  _message = null;
                  _isLoading = false;
                });
              },
              onSubmitted: (_) => _searchProduct(),
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                hintText: 'Buscar producto o código SKU',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_searchText.isNotEmpty)
                      IconButton(
                        tooltip: 'Limpiar búsqueda',
                        onPressed: _clearSearch,
                        icon: const Icon(Icons.close),
                      ),
                    IconButton(
                      tooltip: 'Escanear SKU con cámara',
                      onPressed: _scanSku,
                      icon: const Icon(
                        Icons.qr_code_scanner,
                        color: AppColors.primary,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isLoading ? null : _searchProduct,
                icon: const Icon(Icons.search),
                label: const Text('Buscar producto'),
              ),
            ),

            const SizedBox(height: 24),

            if (_isLoading)
              const Center(
                child: Column(
                  children: [
                    CircularProgressIndicator(color: AppColors.primary),
                    SizedBox(height: 16),
                    Text('Consultando inventario...'),
                  ],
                ),
              )
            else if (_product != null)
              _ProductCard(product: _product!)
            else
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      Icon(
                        _message == null
                            ? Icons.inventory_2_outlined
                            : Icons.info_outline,
                        size: 56,
                        color: AppColors.primary,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        _message ??
                            'Escanea un QR o escribe un SKU '
                                'para consultar el inventario.',
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _ProductCard extends StatelessWidget {
  final Map<String, dynamic> product;

  const _ProductCard({required this.product});

  @override
  Widget build(BuildContext context) {
    final name = product['name']?.toString() ?? 'Sin nombre';

    final sku = product['sku']?.toString() ?? 'Sin SKU';

    final quantity = product['quantity']?.toString() ?? '—';

    final unit = product['unit']?.toString() ?? '—';

    final description = product['description']?.toString() ?? '';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'PRODUCTO ENCONTRADO',
              style: TextStyle(
                color: AppColors.success,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              name,
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'SKU: $sku',
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            const Divider(height: 32),
            Row(
              children: [
                Expanded(
                  child: _InfoValue(label: 'EXISTENCIAS', value: quantity),
                ),
                Expanded(
                  child: _InfoValue(label: 'UNIDAD', value: unit),
                ),
              ],
            ),
            if (description.isNotEmpty) ...[
              const Divider(height: 32),
              Text(
                description,
                style: const TextStyle(color: AppColors.textSecondary),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _InfoValue extends StatelessWidget {
  final String label;
  final String value;

  const _InfoValue({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
        ),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(fontSize: 23, fontWeight: FontWeight.bold),
        ),
      ],
    );
  }
}
