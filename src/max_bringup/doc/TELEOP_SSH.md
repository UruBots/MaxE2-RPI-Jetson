# Teleop CM-550: teclado, TTY, SSH y `DISPLAY`

`teleop_cm550_launch.py` arranca `teleop_twist_keyboard`, `twist_to_motion_node` y `cm550_remocon_bridge_node`. El nodo de teclado necesita un **terminal interactivo (TTY)** y, si se lanza con un **prefijo gráfico** (`xterm`, `gnome-terminal`), también un **servidor X** (`DISPLAY`).

## Errores frecuentes

| Mensaje | Causa | Qué hacer |
|--------|--------|-----------|
| `termios.error` / *Inappropriate ioctl for device* | `ros2 launch` no da TTY al proceso hijo | `teleop_prefix` con terminal, o `include_teleop:=false` + teleop en otra sesión con `ssh -t` (ver abajo) |
| `DISPLAY is not set` / *Can't open display* | `xterm` (o similar) por **SSH sin X11** | No usar prefijos gráficos en SSH “pelo”; usar `include_teleop:=false` o `ssh -X` |
| `No such file or directory: 'xterm'` | Paquete no instalado | `sudo apt install xterm` o usar `gnome-terminal -- ` en escritorio GNOME |
| `ros2: command not found` (remoto) | No se cargó el setup de ROS en esa línea | Comprobar rutas `/opt/ros/humble/setup.bash` y `~/ros2_ws/install/setup.bash` en la **RPi**; usar la ruta absoluta al YAML (ver abajo) |
| `Couldn't parse params file` / ruta `/share/max_bringup/...` | `$(ros2 pkg prefix max_bringup)` se ejecutó en **tu PC** (comillas mal) | Usar **comillas simples** en todo el comando `ssh '...'` o **ruta absoluta** al YAML en la RPi (ver § Comillas) |
| Teclas OK pero el robot no se mueve | `twist_to_motion` publicaba en `/max/motion_cmd_teleop` y el puente solo en `/max/motion_cmd` (sin `motion_mux`) | Actualizar `max_bringup` y `colcon build`: el launch `teleop_cm550` ya envía a `/max/motion_cmd`. Comprueba: `ros2 topic echo /max/motion_cmd` al pulsar teclas; firmware CM-550 en Play + `rc.read()` |

## Opción A — Escritorio local en la robot (monitor / sesión gráfica)

Con sesión gráfica en la misma máquina:

```bash
ros2 launch max_bringup teleop_cm550_launch.py teleop_prefix:='xterm -hold -e '
# requiere: sudo apt install xterm
```

En **Ubuntu Desktop** con GNOME (sin `xterm`):

```bash
ros2 launch max_bringup teleop_cm550_launch.py teleop_prefix:='gnome-terminal -- '
```

Si solo entras por SSH pero hay usuario con sesión gráfica en el monitor, a veces:

```bash
export DISPLAY=:0
ros2 launch max_bringup teleop_cm550_launch.py teleop_prefix:='xterm -hold -e '
```

(sujeto a permisos X / `xhost`.)

## Opción B — SSH con reenvío X11 (ventana en tu PC)

Desde **tu PC** (con servidor X: Linux nativo, WSLg, XQuartz en macOS, etc.):

```bash
ssh -X usuario@IP_ROBOT
# o: ssh -Y usuario@IP_ROBOT
echo $DISPLAY    # debe mostrar algo (p. ej. localhost:10.0)
ros2 launch max_bringup teleop_cm550_launch.py teleop_prefix:='xterm -hold -e '
```

La ventana de `xterm` se abre en **tu** pantalla.

## Opción C — SSH sin gráficos (recomendado en headless)

No uses `xterm` ni `gnome-terminal` en el remoto: no hay `DISPLAY`.

### 1) Lanzar solo el mapper y el puente Remocon

```bash
ros2 launch max_bringup teleop_cm550_launch.py include_teleop:=false
```

Eso deja corriendo `twist_to_motion_node` y `cm550_remocon_bridge_node`.

### 2) Teleop en otra terminal con TTY real

El flag **`-t`** de SSH asigna pseudo-TTY (necesario para leer teclas).

**Segunda terminal** (desde tu PC). En la **RPi** debe existir el workspace instalado y el usuario debe coincidir (sustituye `ubuntu` y la ruta si hace falta):

```bash
ssh -t ubuntu@IP_ROBOT 'bash -lc "source /opt/ros/humble/setup.bash && source /home/ubuntu/ros2_ws/install/setup.bash && ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --params-file /home/ubuntu/ros2_ws/install/max_bringup/share/max_bringup/config/cm550_motion_bridge_max_e2.yaml"'
```

Ruta **absoluta** al YAML: evita ambigüedades. Si tu usuario en la RPi no es `ubuntu`, cambia `/home/ubuntu` por `/home/tu_usuario`.

#### Comillas y `$(ros2 pkg prefix …)` (importante)

Si escribes el comando así, con **comillas dobles** envolviendo todo lo que va a `ssh`:

```bash
ssh -t ubuntu@IP "bash -lc \"... --params-file \$(ros2 pkg prefix max_bringup)/...\""
```

entonces **`$(ros2 pkg prefix max_bringup)` se ejecuta en tu PC**. Si allí no tienes `max_bringup` instalado, queda vacío y el path pasa a ser algo como `/share/max_bringup/...` → error al abrir el YAML.

**Solución:** usa **comillas simples** envolviendo **todo** lo que pasas a `ssh` (desde `bash -lc` hasta el final), para que `$(ros2 pkg prefix …)` no se evalúe en tu PC. Más simple: **ruta absoluta** al YAML en la RPi, como en el ejemplo principal.

Si quieres `$(ros2 pkg prefix max_bringup)` resuelto en la RPi, el truco es exactamente ese: comillas simples en el `ssh` exterior. Comprueba con `echo`:

```bash
ssh ubuntu@IP_ROBOT 'echo $(ros2 pkg prefix max_bringup)'
```

(debe imprimir la ruta **del robot**, no vacío).

Mismo equipo, dos ventanas SSH: en una el `launch` con `include_teleop:=false`, en la otra el `ros2 run ...` con `ssh -t`.

## Argumentos del launch (resumen)

| Argumento | Uso |
|-----------|-----|
| `teleop_prefix` | Comando previo al ejecutable del teleop (p. ej. `xterm -hold -e ` con espacio final). Requiere `DISPLAY` si es terminal gráfico. |
| `include_teleop` | `false`: no arranca `teleop_twist_keyboard` dentro del launch (para combinar con sesión `ssh -t` o evitar fallos sin X11). |
| `config_file` | YAML compartido (por defecto `cm550_motion_bridge_max_e2.yaml`). |

## Ver también

- Índice de launchers: [LAUNCHERS.md](LAUNCHERS.md)
