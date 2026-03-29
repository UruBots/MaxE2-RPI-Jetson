# De la flecha del teleop a las páginas de motion (101, 103, …)

Cadena completa con `teleop_cm550_launch.py`:

```
Tecla (p. ej. i = adelante)
  → teleop_twist_keyboard publica /cmd_vel (geometry_msgs/Twist)
  → twist_to_motion_node traduce Twist → nombre de acción (std_msgs/String en /max/motion_cmd)
  → cm550_remocon_bridge_node mapea el nombre → página(s) motion y envía bytes Remocon por USB/UART
  → firmware en la CM-550 (rc.read()) recibe un valor entero y llama motion.play(...)
```

## Qué significa cada capa

### 1. Teclado → `forward_command`

En `cm550_motion_bridge_max_e2.yaml`, bloque `twist_to_motion_node`:

- `forward_command: 'walk'` — la flecha **adelante** publica el string **`walk`** (no el número de página).
- `backward_command: 'reverse'`, `left_command: 'turn_left'`, etc.

Puedes cambiar `'walk'` por otro nombre siempre que exista en `command_map`.

### 2. Nombre → número de página (`command_map`)

El puente lee `command_map`, por ejemplo:

`walk:103` → la acción `walk` se traduce a la **página motion 103**.

### 3. Secuencias (`command_sequences`) — prioridad sobre el mapa

Si el **mismo** nombre aparece en `command_sequences`, el puente **no** usa solo `command_map` para ese nombre: envía **varias** páginas en serie (p. ej. `101|103`) con `sequence_step_delay_sec` entre medias.

En el firmware de referencia [`docs/01_ENG2_Max_E2_PY_ros2_ready.py`](../../docs/01_ENG2_Max_E2_PY_ros2_ready.py), para el valor Remocon **10000 + 103** ya se hace:

`Motion_Play(101, 103)`

Es decir: **un solo paquete con página 103** basta para la marcha tipo “walk” si ese script es el que corre en la CM-550. Por eso en el YAML por defecto **walk** y **follow** están solo en `command_map` (página 103) y **no** en `command_sequences`: evita mandar antes un `101` suelto que en el firmware sería `Motion_Play(101)` sin segundo argumento.

`reverse`, `turn_left` y `turn_right` usan por defecto **una sola página** en `command_map` (`reverse:158`, `turn_left:50`, `turn_right:51`). Solo la página **103** tiene caso especial en el firmware de referencia (`Motion_Play(101,103)`); el resto llama `Motion_Play(página)`.

### Tabla teleop estándar (`teleop_twist_keyboard`)

| Tecla | Efecto en `/cmd_vel` | String en `/max/motion_cmd` | Página(s) por defecto |
|-------|----------------------|-----------------------------|------------------------|
| **i** | `linear.x > 0` | `walk` | 103 |
| **,** | `linear.x < 0` | `reverse` | 158 |
| **j** | `angular.z > 0` (izquierda) | `turn_left` | 50 |
| **l** | `angular.z < 0` (derecha) | `turn_right` | 51 |
| Suelta | ~0 | `stop` | 1 |

`twist_to_motion_node` prioriza **marcha atrás/adelante** cuando `|linear| >= |angular|`, y el giro cuando el angular domina (y `prefer_turn_over_forward: true`), para que **,** no quede bloqueada por ruido angular.

### 4. Valor por el cable (Remocon)

El nodo envía paquetes `FF 55` + valor 16-bit. Para motions:

`valor = 10000 + número_de_página`

(equivalente a `MOTION_BASE + page` en el bridge).

Ejemplo: página **103** → valor **10103** → el log del nodo muestra `Remocon enviado: value=10103 ...`.

## Comprobar que la cadena funciona

1. `ros2 topic echo /cmd_vel` — **i** → `linear.x > 0`; **,** → `linear.x < 0`; **j**/**l** → `angular.z` distinto de 0.
2. `ros2 topic echo /max/motion_cmd` — `walk` / `reverse` / `turn_left` / `turn_right` según la tabla.
3. Log de `cm550_remocon_bridge_node`: líneas `Remocon enviado: value=...`.
4. En la CM-550: modo Play, script con `rc.read()` corriendo, USB correcto (`port` en el YAML).

## Ajustar páginas a tu `.mtn3`

Edita `command_map` para que los números coincidan con las páginas reales del robot. Puedes extraer un borrador con:

`python3 scripts/extract_cm550_motion_map.py ruta/al/archivo.mtn3`

## Si “se envía” pero no se mueve

- Páginas distintas a las cargadas en la CM-550.
- Script distinto al de referencia (otro manejo de `10000 + page`).
- `ignore_unknown_commands: true` y el nombre del string no está en el mapa (mira logs; sube a `warn` temporalmente).
- Reenvío: con `republish_interval_sec` > 0 en `twist_to_motion_node` se repite el mismo comando mientras mantienes el Twist (por si el firmware espera refresco).
