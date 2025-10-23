## 📝 Descripción

Breve descripción de los cambios realizados en este PR.

<!-- Proporciona un resumen claro de qué cambios introduces y por qué -->

## 🔗 Issue Relacionado

Fixes #(número de issue)
<!-- Si este PR resuelve un issue, reemplaza el número arriba -->
<!-- Si no hay issue relacionado, explica la motivación para este cambio -->

## 🧪 Tipo de Cambio

Por favor marca las opciones relevantes:

- [ ] 🐛 Bug fix (cambio que corrige un issue sin romper funcionalidad existente)
- [ ] ✨ Nueva funcionalidad (cambio que agrega funcionalidad sin romper existente)
- [ ] 💥 Breaking change (cambio que causa que funcionalidad existente no funcione como se esperaba)
- [ ] 📚 Documentación (cambio solo en documentación)
- [ ] 🎨 Refactoring (cambio de código que no corrige bug ni agrega funcionalidad)
- [ ] ⚡ Performance (cambio que mejora performance)
- [ ] 🧪 Tests (agregar tests faltantes o corregir tests existentes)
- [ ] 🔧 Chore (cambios en build process, herramientas auxiliares, etc.)

## 🧪 Testing

Describe las pruebas que realizaste para verificar tus cambios:

- [ ] Tests unitarios pasan (`pytest tests/`)
- [ ] Tests de integración pasan
- [ ] Tests manuales realizados
- [ ] Verificado en entorno local
- [ ] Verificado con Docker
- [ ] Probado comandos Slack afectados

### 🧪 Detalles de Testing

<!-- Describe específicamente qué probaste -->

**Comandos probados:**
- [ ] `/help`
- [ ] `/analyze`
- [ ] `/generate`
- [ ] Otros: ___________

**Escenarios probados:**
- [ ] Configuración básica
- [ ] Manejo de errores
- [ ] Casos edge
- [ ] Performance con datos grandes

## 📋 Checklist

- [ ] Mi código sigue las guías de estilo del proyecto (PEP 8, Black, isort)
- [ ] He realizado self-review de mi código
- [ ] He comentado mi código, especialmente en áreas complejas
- [ ] He actualizado la documentación correspondiente
- [ ] Mis cambios no generan nuevos warnings o errores
- [ ] He agregado tests que prueban mi fix/funcionalidad
- [ ] Tests nuevos y existentes pasan localmente
- [ ] Cualquier cambio dependiente ha sido mergeado y publicado

## 🔒 Checklist de Seguridad

- [ ] No he expuesto API keys, tokens, o información sensible
- [ ] He validado inputs de usuario apropiadamente
- [ ] He considerado implicaciones de seguridad de mis cambios
- [ ] No he introducido vulnerabilidades conocidas

## 📊 Impacto en Performance

- [ ] No hay impacto en performance
- [ ] Mejora performance
- [ ] Podría impactar performance (explicar abajo)

<!-- Si hay impacto en performance, explica: -->

## 🗄️ Cambios en Base de Datos

- [ ] No hay cambios en BD
- [ ] Cambios compatibles hacia atrás
- [ ] Requiere migración (incluir script)

<!-- Si hay cambios en BD, describe: -->

## 📚 Cambios en Documentación

- [ ] README.md actualizado
- [ ] API_DOCUMENTATION.md actualizado
- [ ] CHANGELOG.md actualizado
- [ ] Comentarios en código agregados/actualizados
- [ ] No se requieren cambios en documentación

## 🐳 Cambios en Docker/Deployment

- [ ] No hay cambios en deployment
- [ ] Dockerfile actualizado
- [ ] docker-compose.yml actualizado
- [ ] Variables de entorno nuevas (actualizar .env.example)
- [ ] Cambios en requirements.txt

## 🔄 Compatibilidad hacia Atrás

- [ ] Cambios son completamente compatibles hacia atrás
- [ ] Cambios requieren actualización de configuración
- [ ] Breaking changes (documentar en CHANGELOG.md)

## 📸 Screenshots/Logs

<!-- Si aplica, agrega screenshots o logs que muestren el cambio -->

**Antes:**
```
<!-- Logs o screenshots del comportamiento anterior -->
```

**Después:**
```
<!-- Logs o screenshots del nuevo comportamiento -->
```

## 🤔 Preguntas para Reviewers

<!-- ¿Hay algo específico en lo que te gustaría que se enfoquen los reviewers? -->

- [ ] ¿La arquitectura propuesta es la correcta?
- [ ] ¿Hay casos edge que no consideré?
- [ ] ¿El manejo de errores es adecuado?
- [ ] ¿La documentación es clara?
- [ ] Otros: ___________

## 📎 Información Adicional

<!-- Cualquier información adicional que pueda ser útil para los reviewers -->

### Referencias
- Link a documentación relevante
- Issues relacionados
- PRs relacionados

### Notas para Deployment
- Pasos especiales requeridos
- Orden de deployment si hay dependencias
- Rollback plan si algo sale mal

---

**Para Maintainers:**

### 🏷️ Labels Sugeridos
<!-- Los maintainers pueden agregar labels apropiados -->
- `bug` / `enhancement` / `documentation` / `refactor`
- `priority: high` / `priority: medium` / `priority: low`
- `size: small` / `size: medium` / `size: large`
- `needs-review` / `ready-to-merge`

### 🎯 Milestone
<!-- Asignar a milestone apropiado si aplica -->

### 👥 Reviewers Sugeridos
<!-- @mention a reviewers específicos si es necesario -->