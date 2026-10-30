

\# LIA TRACE



Sistema de trazabilidad logística e integración ERP.



\## Versión

0.1.0 - Desarrollo inicial



\## Descripción



LIA TRACE es una plataforma de trazabilidad logística

diseñada para registrar, consultar y supervisar

movimientos de productos.



El proyecto contempla su implementación inicial

para ALCORE Puertas y Ventanas.



\## Tecnologías



\- Flutter / Dart - Aplicación Android

\- Python / FastAPI - Backend

\- PostgreSQL - Base de datos

\- Docker - Infraestructura

\- Odoo - Integración ERP

\- REST API - Comunicación



\## Arquitectura



apps/mobile

&#x20;   Aplicación Android.



backend

&#x20;   API, seguridad y lógica de negocio.



database

&#x20;   Recursos de base de datos.



shared

&#x20;   Contratos y datos de demostración.



infrastructure

&#x20;   Configuración de servicios.



docs

&#x20;   Documentación técnica.



scripts

&#x20;   Automatización del desarrollo.



\## Módulos



1\. Autenticación

2\. Dashboard

3\. Escáner de códigos

4\. Inventario

5\. Recepción

6\. Embarques

7\. Entregas

8\. Incidencias

9\. Evidencias

10\. Historial

11\. Sincronización



\## Integración ERP



El sistema contará con dos modos:



MOCK:

Datos simulados para desarrollo y demostración.



ODOO:

Integración real con el ERP del cliente.



La conexión real se configurará cuando se

conozcan la versión y los permisos disponibles.



\## Estado



Proyecto en desarrollo.

La estructura inicial no constituye todavía

una aplicación ejecutable.
