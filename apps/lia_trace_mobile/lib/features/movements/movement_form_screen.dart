import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../../core/theme/app_colors.dart';
import '../scanner/sku_scanner_screen.dart';

enum InventoryOperation { entry, exit }

class MovementFormScreen extends StatefulWidget {
  final InventoryOperation operation;

  const MovementFormScreen({super.key, required this.operation});

  @override
  State<MovementFormScreen> createState() => _MovementFormScreenState();
}

class _MovementFormScreenState extends State<MovementFormScreen> {
  static const String _baseUrl = 'http://192.168.1.65:8000/api/v1';

  final _skuController = TextEditingController();
  final _quantityController = TextEditingController();
  final _referenceController = TextEditingController();
  final _notesController = TextEditingController();
  final _skuFocus = FocusNode();

  Map<String, dynamic>? _product;
  String? _message;
  bool _searching = false;
  bool _submitting = false;
  bool _requiresVerification = false;
  int _searchVersion = 0;
  String? _pendingKey;

  bool get _isEntry => widget.operation == InventoryOperation.entry;

  String get _title =>
      _isEntry ? 'Entrada de inventario' : 'Salida de inventario';

  Color get _operationColor => _isEntry ? AppColors.success : AppColors.danger;

  String get _movementType => _isEntry ? 'ENTRY' : 'EXIT';

  @override
  void dispose() {
    _skuController.dispose();
    _quantityController.dispose();
    _referenceController.dispose();
    _notesController.dispose();
    _skuFocus.dispose();
    super.dispose();
  }

  String _newIdempotencyKey() {
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));
    final hex = bytes.map((value) => value.toRadixString(16).padLeft(2, '0'));
    return hex.join();
  }

  void _invalidateProduct() {
    _searchVersion++;
    setState(() {
      _product = null;
      _message = null;
      _searching = false;
      _pendingKey = null;
    });
  }

  Future<void> _searchProduct() async {
    if (_submitting || _requiresVerification) return;

    FocusScope.of(context).unfocus();

    final sku = _skuController.text.trim();
    final version = ++_searchVersion;

    setState(() {
      _product = null;
      _message = null;
      _searching = sku.isNotEmpty;
      _pendingKey = null;
    });

    if (sku.isEmpty) {
      setState(() => _message = 'Escribe o escanea un SKU.');
      return;
    }

    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/inventory'))
          .timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        throw Exception('Error HTTP ${response.statusCode}');
      }

      final data = jsonDecode(response.body);
      if (data is! List) {
        throw const FormatException('Respuesta de inventario inválida.');
      }

      Map<String, dynamic>? found;

      for (final item in data) {
        if (item is Map<String, dynamic> &&
            item['sku']?.toString().trim().toLowerCase() == sku.toLowerCase()) {
          found = item;
          break;
        }
      }

      if (!mounted || version != _searchVersion) return;

      setState(() {
        _product = found;
        _searching = false;
        _message = found == null ? 'Producto no encontrado: $sku' : null;
      });
    } catch (error) {
      if (!mounted || version != _searchVersion) return;

      setState(() {
        _searching = false;
        _message = 'No se pudo consultar el inventario:\n$error';
      });
    }
  }

  Future<void> _scanSku() async {
    if (_submitting || _requiresVerification) return;

    FocusScope.of(context).unfocus();

    final sku = await Navigator.of(context).push<String>(
      MaterialPageRoute<String>(builder: (_) => const SkuScannerScreen()),
    );

    if (!mounted || sku == null || sku.trim().isEmpty) return;

    _skuController.text = sku.trim();
    _invalidateProduct();

    await Future<void>.delayed(const Duration(milliseconds: 500));

    if (!mounted || _skuController.text.trim() != sku.trim()) return;

    await _searchProduct();
  }

  String? _validateQuantity(String text) {
    final value = text.trim();

    if (!RegExp(r'^\d+(\.\d{1,3})?$').hasMatch(value)) {
      return 'Introduce una cantidad positiva con máximo 3 decimales.';
    }

    final number = num.tryParse(value);
    if (number == null || !number.isFinite || number <= 0) {
      return 'La cantidad debe ser mayor que cero.';
    }

    if (number > 99999999999.999) {
      return 'La cantidad supera el límite permitido.';
    }

    if (!_isEntry && _product != null) {
      final stock = num.tryParse(_product!['quantity'].toString());
      if (stock != null && number > stock) {
        return 'Existencias insuficientes.';
      }
    }

    return null;
  }

  Future<bool> _confirmMovement(String quantity) async {
    final product = _product!;
    final action = _isEntry ? 'ENTRADA' : 'SALIDA';

    return await showDialog<bool>(
          context: context,
          builder: (dialogContext) => AlertDialog(
            title: Text('Confirmar $action'),
            content: Text(
              'Producto: ${product['name']}\n'
              'SKU: ${product['sku']}\n'
              'Cantidad: $quantity ${product['unit']}\n\n'
              'Esta operación modificará las existencias reales.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext, false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(dialogContext, true),
                child: const Text('Confirmar'),
              ),
            ],
          ),
        ) ??
        false;
  }

  Future<void> _registerMovement() async {
    if (_submitting || _requiresVerification || _product == null) return;

    final quantity = _quantityController.text.trim();
    final validation = _validateQuantity(quantity);

    if (validation != null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(validation)));
      return;
    }

    final reference = _referenceController.text.trim();
    if (reference.length > 150) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('La referencia supera 150 caracteres.')),
      );
      return;
    }

    final confirmed = await _confirmMovement(quantity);
    if (!mounted || !confirmed) return;

    final itemId = _product!['id'];
    if (itemId is! int || itemId <= 0) {
      setState(() => _message = 'El producto no tiene un ID válido.');
      return;
    }

    final key = _pendingKey ?? _newIdempotencyKey();
    _pendingKey = key;

    final payload = <String, dynamic>{
      'inventory_item_id': itemId,
      'movement_type': _movementType,
      'quantity': quantity,
      'reference': reference.isEmpty ? null : reference,
      'notes': _notesController.text.trim().isEmpty
          ? null
          : _notesController.text.trim(),
      'idempotency_key': key,
    };

    setState(() {
      _submitting = true;
      _message = null;
    });

    try {
      final response = await http
          .post(
            Uri.parse('$_baseUrl/movements'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 20));

      if (!mounted) return;

      if (response.statusCode == 201) {
        _pendingKey = null;
        _quantityController.clear();
        _referenceController.clear();
        _notesController.clear();

        setState(() {
          _submitting = false;
          _product = null;
          _message =
              'Movimiento registrado correctamente. '
              'Consulta nuevamente el producto para ver el stock actualizado.';
        });

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Movimiento registrado correctamente.')),
        );
        return;
      }

      String detail = 'Error HTTP ${response.statusCode}';
      try {
        final decoded = jsonDecode(response.body);
        if (decoded is Map && decoded['detail'] != null) {
          detail = decoded['detail'].toString();
        }
      } catch (_) {
        // Mantener el mensaje HTTP.
      }

      setState(() {
        _submitting = false;
        _pendingKey = null;
        _message = 'No se registró el movimiento: $detail';
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _submitting = false;
        _requiresVerification = true;
        _message =
            'No se pudo confirmar el resultado del registro.\n'
            'El servidor pudo haber recibido la operación.\n'
            'NO vuelvas a enviarla todavía.\n\n'
            'Revisa los movimientos registrados antes de continuar.\n'
            'Detalle técnico: $error';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final product = _product;
    final locked = _submitting || _requiresVerification;

    return Scaffold(
      appBar: AppBar(title: Text(_title)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Row(
              children: [
                Icon(
                  _isEntry ? Icons.add_box_outlined : Icons.outbox_outlined,
                  color: _operationColor,
                  size: 32,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _title,
                    style: const TextStyle(
                      fontSize: 23,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'Escanea un QR o introduce el SKU del material.',
              style: TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: _skuController,
              focusNode: _skuFocus,
              enabled: !locked,
              onTap: () {
                _skuController.selection = TextSelection(
                  baseOffset: 0,
                  extentOffset: _skuController.text.length,
                );
              },
              onChanged: (_) => _invalidateProduct(),
              onSubmitted: (_) => _searchProduct(),
              decoration: InputDecoration(
                labelText: 'Código SKU',
                hintText: 'Ej. ALC-VENT-001',
                prefixIcon: const Icon(Icons.inventory_2_outlined),
                suffixIcon: IconButton(
                  tooltip: 'Escanear QR',
                  onPressed: locked ? null : _scanSku,
                  icon: const Icon(Icons.qr_code_scanner),
                ),
              ),
            ),
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: locked || _searching ? null : _searchProduct,
                icon: const Icon(Icons.search),
                label: const Text('Buscar producto'),
              ),
            ),
            const SizedBox(height: 20),
            if (_searching)
              const Center(child: CircularProgressIndicator())
            else if (product != null) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'PRODUCTO SELECCIONADO',
                        style: TextStyle(
                          color: _operationColor,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        product['name']?.toString() ?? 'Sin nombre',
                        style: const TextStyle(
                          fontSize: 21,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'SKU: ${product['sku']}',
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                      const Divider(height: 28),
                      Text(
                        'Existencias actuales: ${product['quantity']} '
                        '${product['unit']}',
                        style: const TextStyle(fontSize: 17),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),
              TextField(
                controller: _quantityController,
                enabled: !locked,
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                decoration: InputDecoration(
                  labelText: 'Cantidad',
                  hintText: 'Ej. 2 o 2.500',
                  suffixText: product['unit']?.toString(),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _referenceController,
                enabled: !locked,
                maxLength: 150,
                decoration: const InputDecoration(
                  labelText: 'Referencia (opcional)',
                  hintText: 'Factura, orden o folio',
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _notesController,
                enabled: !locked,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Notas (opcional)',
                  hintText: 'Observaciones del movimiento',
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: locked ? null : _registerMovement,
                  icon: Icon(
                    _isEntry
                        ? Icons.add_circle_outline
                        : Icons.remove_circle_outline,
                  ),
                  label: Text(
                    _isEntry ? 'Registrar entrada' : 'Registrar salida',
                  ),
                  style: FilledButton.styleFrom(
                    backgroundColor: _operationColor,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
              ),
            ],
            if (_message != null) ...[
              const SizedBox(height: 20),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Text(
                    _message!,
                    style: const TextStyle(color: AppColors.textSecondary),
                  ),
                ),
              ),
            ],
            if (_requiresVerification) ...[
              const SizedBox(height: 12),
              const Text(
                'Registro bloqueado por seguridad. '
                'Verifica el historial antes de realizar otra operación.',
                style: TextStyle(color: AppColors.warning),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
