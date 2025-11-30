# Guía de Presentación - Versión Corta (2 minutos)

## ESTRUCTURA RÁPIDA

### INTRODUCCIÓN (10 segundos)
"Implementé dos funcionalidades: autocompactación y paginación de memoria, y sistema de prioridades de procesos."

---

## PARTE 1: MEMORIA (50 segundos)

### Autocompactación (20 segundos)
1. **Ir a "Gestión de Memoria"**
2. **Decir:** "La autocompactación reorganiza automáticamente la memoria cuando la fragmentación supera 30%."
3. **Mostrar:** Señalar la estadística "Frag" y el botón "Compactar Memoria"
4. **Acción rápida:** Clic en "Compactar" para mostrar el efecto visual

### Paginación (30 segundos)
1. **Desplazar a tabla "Estadísticas de Paginación"**
2. **Decir:** "Tres algoritmos de reemplazo ejecutándose en paralelo: FIFO, LRU y Optimal."
3. **Señalar métricas:** "Page Faults, Hits y Tasa de Faults - podemos comparar rendimiento en tiempo real."
4. **Dejar correr 2-3 segundos** para que vean números cambiando

---

## PARTE 2: PRIORIDADES (60 segundos)

### Asignación Automática (15 segundos)
1. **Ir a "Gestión de Procesos"**
2. **Señalar columna "Prioridad"**
3. **Decir:** "Prioridades automáticas basadas en tamaño, duración y uso de CPU. 0 es mayor prioridad."

### Algoritmos de Planificación (45 segundos)
1. **Reiniciar simulación** (rápido)
2. **Seleccionar "Priority"** en configuración
3. **Consola - crear procesos:**
   ```
   create 16 50 0
   create 16 50 9
   ```
4. **Decir:** "Proceso prioridad 0 preempta al de prioridad 9."
5. **Mostrar log:** "Aquí vemos el mensaje de preemption."
6. **Mencionar aging:** "Procesos que esperan >20 ticks aumentan prioridad automáticamente para evitar inanición."

---

## CIERRE (10 segundos)
"Estas implementaciones hacen el simulador más realista y permiten estudiar conceptos avanzados de SO."

**TOTAL: ~2 minutos**

---

## VERSIÓN ULTRA-RÁPIDA (Si te quedas sin tiempo)

### Opción A: Solo mostrar (1 minuto)
1. **Memoria:** Ir a "Gestión de Memoria" → Señalar tabla de paginación → "Tres algoritmos comparándose"
2. **Prioridades:** Ir a "Gestión de Procesos" → Señalar columna Prioridad → "Asignación automática y algoritmos Priority/PriorityRR disponibles"

### Opción B: Una demo rápida (1.5 minutos)
1. **Mostrar paginación:** Tabla con estadísticas cambiando
2. **Crear proceso con prioridad:** `create 16 50 0` → Mostrar que se ejecuta primero

---

## COMANDOS PRE-PARADOS (copiar y pegar rápido)

```
create 16 50 0
create 16 50 9
```

---

## CHECKLIST RÁPIDO

- [ ] App abierta y funcionando
- [ ] Velocidad en 1000ms (visible pero rápido)
- [ ] Comandos listos para copiar
- [ ] Saber dónde están las tablas (paginación y procesos)
- [ ] Practicar el flujo: Memoria → Prioridades

---

## FRASES CLAVE (memorizar)

1. "Autocompactación cuando fragmentación > 30%"
2. "Tres algoritmos de paginación: FIFO, LRU, Optimal"
3. "Prioridades 0-9, asignación automática"
4. "Priority preemptivo con aging para evitar inanición"

---

## ESTRATEGIA DE PRESENTACIÓN

### Si tienes tiempo completo (2 min):
- Muestra ambas partes completas
- Una demo rápida de cada funcionalidad

### Si te quedas corto de tiempo:
- Prioriza mostrar la interfaz
- Menciona las funcionalidades sin demo profunda
- "Puedo mostrar más detalles después si hay preguntas"

### Si hay preguntas:
- Responde breve: "Sí, la autocompactación es configurable"
- "El aging se aplica cada 10 ticks"
- "Puedo mostrar más después si quieren"

---

## FLUJO VISUAL RÁPIDO

```
1. Abrir app (ya debe estar lista)
   ↓
2. Click "Gestión de Memoria"
   ↓
3. Señalar tabla "Estadísticas de Paginación" (15 seg)
   ↓
4. Click "Gestión de Procesos"
   ↓
5. Señalar columna "Prioridad" (10 seg)
   ↓
6. Reiniciar → Seleccionar "Priority"
   ↓
7. Consola: create 16 50 0 y create 16 50 9 (30 seg)
   ↓
8. Mostrar preemption en log (15 seg)
   ↓
9. Cierre (10 seg)
```

---

## ERRORES A EVITAR

❌ No crear procesos manualmente durante la demo (tarda mucho)
❌ No explicar código interno
❌ No entrar en detalles técnicos profundos
✅ Mostrar la interfaz
✅ Mencionar conceptos clave
✅ Una demo rápida y visual

---

**RECUERDA: En 2 minutos, mostrar > explicar**

