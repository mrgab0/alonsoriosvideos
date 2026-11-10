---
name: visual-auditor
description: >-
  Auditoría visual, contraste y monitoreo sintético Playwright en la nube vía Checkly.
  Ejecuta checks de UI, accesibilidad y capturas sin consumir RAM ni CPU local.
---

# Visual Auditor Skill (Checkly Cloud Playwright)

Permite ejecutar y verificar pruebas visuales, contrastes, temas oscuros y flujos de usuario (DOM, formularios, autenticación) utilizando los ejecutores de **Playwright en la nube de Checkly**, protegiendo el hardware local (Dual-Core / Termux) según la regla de Hardware Limits.

## Credenciales en Bóveda SQLite (`vault`)
- `CHECKLY_ACCOUNT_ID`: `f2caf3ea-620a-49e2-86ef-a8cd7955ee45`
- `CHECKLY_API_KEY`: Servicio de API para ejecución y consulta.
- `CHECKLY_USER_API_KEY`: Token de usuario administrativo.

## Checks Activos en la Nube
1. **Bonbon Flowers Storefront:** Visual Eyes, modo oscuro, contraste y grid de catálogo (`36ec983b-663c-412c-b47e-e6892b6b940b`).
2. **Gabriela's Flowers:** Visual Eyes y validación de widget chatbot (`1ee2ade2-5ba5-4505-88b4-417105ce5412`).
3. **aldri.shop:** Visual Eyes y verificación de temas (`c224af8b-e557-41e7-b327-c559ac3555f0`).
4. **Lead Softphone:** Visual Eyes, formulario de login, CRM y dialer (`4049db66-21f2-40ee-86bd-d993c6e514d5`).

## Comandos Operativos

### 1. Listar todos los checks y estados
```bash
python ~/.gemini/config/plugins/antigravity-autopilot/scripts/checkly_runner.py list
```

### 2. Disparar un check en Checkly Cloud tras desplegar a Vercel
```bash
python ~/.gemini/config/plugins/antigravity-autopilot/scripts/checkly_runner.py trigger <CHECK_ID>
```

### 3. Consultar el último resultado de ejecución
```bash
python ~/.gemini/config/plugins/antigravity-autopilot/scripts/checkly_runner.py status <CHECK_ID>
```
