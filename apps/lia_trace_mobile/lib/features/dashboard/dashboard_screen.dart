import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../inventory/inventory_screen.dart';
import '../movements/movement_form_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  void _openMovement(BuildContext context, InventoryOperation operation) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => MovementFormScreen(operation: operation),
      ),
    );
  }

  void _showComingSoon(BuildContext context, String label) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$label: próximamente'),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _onNavigationSelected(BuildContext context, int index) {
    if (index == 0) {
      return;
    }

    if (index == 1) {
      Navigator.of(
        context,
      ).push(MaterialPageRoute<void>(builder: (_) => const InventoryScreen()));
      return;
    }

    _showComingSoon(context, 'Sección');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'LIA TRACE',
          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.5),
        ),
        actions: const [
          Padding(
            padding: EdgeInsets.only(right: 16),
            child: Icon(Icons.notifications_outlined),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'ALCORE · OPERACIONES',
                    style: TextStyle(
                      color: AppColors.primary,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                  SizedBox(height: 12),
                  Text(
                    'Tu inventario en la palma de tu mano',
                    style: TextStyle(fontSize: 23, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Control y trazabilidad desde cualquier lugar',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Acciones rápidas',
              style: TextStyle(fontSize: 19, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 14),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 1.65,
              children: [
                _ActionTile(
                  label: 'Escanear',
                  icon: Icons.qr_code_scanner,
                  color: AppColors.primary,
                  onTap: () => _showComingSoon(context, 'Escanear'),
                ),
                _ActionTile(
                  label: 'Foto',
                  icon: Icons.camera_alt_outlined,
                  color: AppColors.primary,
                  onTap: () => _showComingSoon(context, 'Foto'),
                ),
                _ActionTile(
                  label: 'Entrada',
                  icon: Icons.add_box_outlined,
                  color: AppColors.success,
                  onTap: () => _openMovement(context, InventoryOperation.entry),
                ),
                _ActionTile(
                  label: 'Salida',
                  icon: Icons.outbox_outlined,
                  color: AppColors.danger,
                  onTap: () => _openMovement(context, InventoryOperation.exit),
                ),
              ],
            ),
            const SizedBox(height: 24),
            const Text(
              'Resumen de inventario',
              style: TextStyle(fontSize: 19, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 14),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Productos registrados',
                            style: TextStyle(color: AppColors.textSecondary),
                          ),
                          SizedBox(height: 8),
                          Text(
                            '—',
                            style: TextStyle(
                              fontSize: 30,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          SizedBox(height: 8),
                          Text(
                            'Pendiente de conectar al backend',
                            style: TextStyle(
                              color: AppColors.textMuted,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Icon(Icons.donut_large, color: AppColors.primary, size: 58),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: 0,
        onDestinationSelected: (index) {
          _onNavigationSelected(context, index);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Inicio',
          ),
          NavigationDestination(
            icon: Icon(Icons.inventory_2_outlined),
            selectedIcon: Icon(Icons.inventory_2),
            label: 'Inventario',
          ),
          NavigationDestination(
            icon: Icon(Icons.camera_alt_outlined),
            selectedIcon: Icon(Icons.camera_alt),
            label: 'Cámara',
          ),
          NavigationDestination(
            icon: Icon(Icons.swap_horiz),
            label: 'Movimientos',
          ),
          NavigationDestination(
            icon: Icon(Icons.bar_chart_outlined),
            selectedIcon: Icon(Icons.bar_chart),
            label: 'Reportes',
          ),
        ],
      ),
    );
  }
}

class _ActionTile extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _ActionTile({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
          ],
        ),
      ),
    );
  }
}
