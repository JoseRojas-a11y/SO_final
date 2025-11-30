# Guía de Presentación - Parte 3 y 4 del Proyecto

## Estructura de la Presentación (10-15 minutos)

### 1. Introducción (1 minuto)

**Qué decir:**
"Mi parte del proyecto consistió en implementar dos funcionalidades principales:
1. **Gestión avanzada de memoria** con autocompactación y algoritmos de paginación
2. **Sistema de prioridades de procesos** con asignación automática y algoritmos de planificación basados en prioridades

Estas implementaciones mejoran significativamente la simulación, acercándola más a sistemas operativos reales."

---

## PARTE 1: GESTIÓN AVANZADA DE MEMORIA (5-7 minutos)

### 1.1 Autocompactación de Memoria

**Qué mostrar:**
1. Abrir la aplicación y seleccionar cualquier algoritmo de planificación.
2. Ir a la pestaña **"Gestión de Memoria"**.

**Qué decir:**
"La primera funcionalidad que implementé es la **autocompactación de memoria**. Este mecanismo reorganiza automáticamente la memoria para reducir la fragmentación externa."

**Demostración:**
1. **Mostrar las barras de memoria:**
   - "Aquí vemos tres algoritmos de asignación ejecutándose en paralelo: First Fit, Best Fit y Worst Fit."
   - "Cada barra muestra bloques verdes (memoria ocupada) y grises (memoria libre)."

2. **Crear fragmentación:**
   - Usar la consola: `create 20 30` varias veces
   - Luego terminar algunos procesos para generar fragmentación
   - "Como pueden ver, ahora tenemos bloques libres intercalados entre bloques ocupados. Esto es fragmentación externa."

3. **Mostrar autocompactación:**
   - Esperar o crear más procesos
   - "Cuando la fragmentación supera el 30%, el sistema automáticamente compacta la memoria."
   - "Observen cómo los bloques ocupados se mueven al inicio y todo el espacio libre queda contiguo al final."
   - Señalar la estadística "Frag" que debería disminuir.

4. **Compactación manual:**
   - Hacer clic en "Compactar Memoria" en uno de los algoritmos
   - "También podemos compactar manualmente para comparar el antes y después."

**Puntos clave a mencionar:**
- "La autocompactación se activa automáticamente cuando la fragmentación supera un umbral configurable (30% por defecto)."
- "También se ejecuta periódicamente cada 50 ticks si hay fragmentación significativa."
- "Esto mejora la eficiencia de asignación y permite asignar procesos que de otra forma no cabrían."

---

### 1.2 Sistema de Paginación

**Qué mostrar:**
1. Seguir en la pestaña "Gestión de Memoria".
2. Desplazarse hasta la tabla **"Estadísticas de Paginación"**.

**Qué decir:**
"La segunda funcionalidad de gestión de memoria es el **sistema de paginación**. Implementé tres algoritmos de reemplazo de páginas que se ejecutan en paralelo para comparar su rendimiento."

**Demostración:**
1. **Explicar la tabla:**
   - "Esta tabla muestra estadísticas de tres algoritmos de reemplazo de páginas: FIFO, LRU y Optimal."
   - "Cada proceso se asigna simultáneamente en los tres algoritmos para poder comparar su rendimiento."

2. **Explicar las métricas:**
   - **Page Faults:** "Número de veces que se necesita cargar una página desde disco (simulado)."
   - **Page Hits:** "Número de accesos exitosos a páginas ya en memoria."
   - **Tasa Faults %:** "Porcentaje de accesos que resultan en page fault. Menor es mejor."
   - **Utilización %:** "Porcentaje de frames físicos utilizados."

3. **Mostrar en acción:**
   - Dejar correr la simulación unos segundos
   - "Observen cómo las estadísticas cambian en tiempo real."
   - "LRU generalmente tiene mejor rendimiento que FIFO porque considera el uso reciente."
   - "Optimal es una heurística que intenta aproximar el algoritmo óptimo teórico."

**Puntos clave a mencionar:**
- "Cada proceso tiene su propia tabla de páginas que mapea páginas lógicas a frames físicos."
- "El sistema simula accesos aleatorios a páginas durante la ejecución, generando page faults cuando es necesario."
- "Esto permite estudiar el comportamiento de diferentes algoritmos de reemplazo en condiciones similares."

---

## PARTE 2: SISTEMA DE PRIORIDADES (5-7 minutos)

### 2.1 Asignación Automática de Prioridades

**Qué mostrar:**
1. Ir a la pestaña **"Gestión de Procesos"**.
2. Observar la columna **"Prioridad"** en la tabla de procesos.

**Qué decir:**
"La primera parte del sistema de prioridades es la **asignación automática**. Todos los procesos generados automáticamente reciben una prioridad calculada basándose en sus características."

**Demostración:**
1. **Mostrar procesos con prioridades:**
   - "Como pueden ver, cada proceso tiene una prioridad entre 0 y 9, donde 0 es la mayor prioridad."
   - "La prioridad se calcula considerando: tamaño del proceso (30%), duración (40%) y uso de CPU (30%)."
   - "Procesos más pequeños, más cortos y menos intensivos reciben mayor prioridad."

2. **Crear procesos manuales con prioridades:**
   - Abrir la consola
   - `create 16 50 0` - "Este proceso tiene prioridad 0, la más alta."
   - `create 16 50 5` - "Este tiene prioridad media."
   - `create 16 50 9` - "Este tiene prioridad baja."
   - "Observen cómo los procesos con prioridad 0 se ejecutan primero."

**Puntos clave:**
- "La asignación automática permite que el sistema priorice procesos más eficientes sin intervención manual."
- "También incluye variación aleatoria para simular diferentes tipos de procesos."

---

### 2.2 Algoritmos de Planificación por Prioridades

**Qué mostrar:**
1. Reiniciar la simulación.
2. En el diálogo de configuración, seleccionar **"Priority"** o **"PriorityRR"**.

**Qué decir:**
"Implementé dos algoritmos nuevos de planificación basados en prioridades, y modifiqué los existentes para considerar prioridades."

**Demostración con Priority:**
1. **Seleccionar "Priority"** en el diálogo de configuración.
2. **Crear procesos con diferentes prioridades:**
   - `create 16 50 9` - Proceso de baja prioridad
   - `create 16 50 0` - Proceso de alta prioridad
   - "Observen cómo el proceso de prioridad 0 preempta al de prioridad 9."

3. **Mostrar preemption:**
   - "En el registro de interrupciones, verán mensajes como 'Process X preempted (Higher priority process)'."
   - "Esto demuestra que el algoritmo es preemptivo."

4. **Explicar aging:**
   - Crear varios procesos de baja prioridad (8-9)
   - Dejar que esperen
   - "Si un proceso espera más de 20 ticks, su prioridad aumenta automáticamente. Esto es el mecanismo de aging que evita la inanición."
   - "Observen cómo la prioridad en la tabla puede cambiar para procesos que esperan mucho."

**Demostración con PriorityRR:**
1. **Reiniciar y seleccionar "PriorityRR"**.
2. **Explicar:**
   - "PriorityRR implementa Round Robin con múltiples colas de prioridad."
   - "Hay una cola por cada nivel de prioridad (0-9)."
   - "Se procesan primero las colas de mayor prioridad, y dentro de cada cola se aplica Round Robin."

**Puntos clave:**
- "Los algoritmos existentes (FCFS, SJF, SRTF, RR) también fueron modificados para considerar prioridades."
- "Priority es preemptivo y tiene aging para evitar inanición."
- "PriorityRR combina las ventajas de prioridades con la equidad de Round Robin."

---

### 2.3 Comparación Visual

**Qué mostrar:**
1. Comparar diferentes algoritmos de planificación.
2. Mostrar cómo afectan las prioridades.

**Qué decir:**
"Para demostrar el impacto de las prioridades, podemos comparar el comportamiento con y sin consideración de prioridades."

**Demostración:**
1. **Ejecutar con FCFS normal:**
   - Crear procesos con diferentes prioridades
   - "Sin considerar prioridades, se ejecutan por orden de llegada."

2. **Ejecutar con Priority:**
   - "Con Priority, los procesos de mayor prioridad se ejecutan primero, independientemente de cuándo llegaron."

3. **Mostrar métricas:**
   - "Observen cómo cambian las métricas: turnaround time, waiting time, etc."
   - "Los procesos de alta prioridad tienen mejor tiempo de respuesta."

---

## RESUMEN Y CIERRE (1-2 minutos)

### Puntos a destacar:

1. **Autocompactación:**
   - Reduce fragmentación externa automáticamente
   - Mejora la eficiencia de asignación de memoria
   - Configurable y transparente para el usuario

2. **Paginación:**
   - Tres algoritmos de reemplazo ejecutándose en paralelo
   - Permite comparar rendimiento en tiempo real
   - Simula comportamiento real de sistemas operativos

3. **Prioridades:**
   - Asignación automática inteligente
   - Dos algoritmos nuevos (Priority, PriorityRR)
   - Algoritmos existentes mejorados
   - Mecanismo de aging para evitar inanición

### Conclusión:

"Estas implementaciones hacen que el simulador sea más realista y educativo, permitiendo estudiar conceptos avanzados de sistemas operativos de manera práctica e interactiva."

---

## CONSEJOS PARA LA PRESENTACIÓN

### Antes de empezar:
- ✅ Asegúrate de tener la aplicación funcionando
- ✅ Ten algunos procesos ya creados para mostrar rápidamente
- ✅ Prepara algunos comandos de consola listos para copiar
- ✅ Verifica que la velocidad de simulación esté en un valor visible (1000-2000ms)

### Durante la presentación:
- ✅ Habla claro y pausado
- ✅ Muestra, no solo expliques - deja que vean la interfaz
- ✅ Usa pausas para que observen los cambios
- ✅ Si algo no funciona como esperado, explica qué debería pasar

### Posibles preguntas y respuestas:

**P: ¿Por qué tres algoritmos de paginación en paralelo?**
R: Para poder comparar su rendimiento en las mismas condiciones. Es más educativo ver cómo se comportan con la misma carga de trabajo.

**P: ¿Cómo funciona el aging exactamente?**
R: Cada 10 ticks, el sistema revisa procesos que esperan más de 20 ticks y reduce su prioridad en 1 (aumenta su importancia). Esto garantiza que eventualmente se ejecuten.

**P: ¿La autocompactación tiene overhead?**
R: Sí, pero es necesario para mantener la eficiencia. Se ejecuta solo cuando es necesario (fragmentación alta) o periódicamente, no en cada tick.

**P: ¿Los algoritmos de prioridades son justos?**
R: Priority puede no ser justo con procesos de baja prioridad, pero el aging mitiga esto. PriorityRR es más justo porque combina prioridades con Round Robin.

---

## CHECKLIST PRE-PRESENTACIÓN

- [ ] Aplicación funciona correctamente
- [ ] Puedo crear procesos manualmente
- [ ] La consola responde a comandos
- [ ] Las tablas se actualizan correctamente
- [ ] Puedo cambiar entre algoritmos de planificación
- [ ] Tengo ejemplos preparados para mostrar
- [ ] Conozco los números clave (30% fragmentación, 20 ticks aging, etc.)
- [ ] He practicado la demostración al menos una vez

---

¡Buena suerte con tu presentación! 🚀

