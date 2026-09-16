# Ejecución independiente en GitHub Actions

La ejecución [35146548569](https://github.com/Lolmastercraft/Avance-2/actions/runs/35146548569) terminó con resultado **success** sobre el commit `1f33768bf9e2751ab478bad1e36cbe68ea1c1193`.

El trabajo instala las herramientas desde cero en Linux, ejecuta el candidato rojo aislado y las fuentes corregidas y conserva ambos reportes como artefacto de GitHub. Una corrida roja esperada no vuelve rojo el trabajo completo: la demostración solo termina correctamente si el candidato inseguro bloquea y las fuentes corregidas permiten.

Las evidencias versionadas en `reportes/roja` y `reportes/verde` corresponden a las ejecuciones locales del mismo pipeline. El documento Word muestra esos resultados. Los resultados independientes del runner Linux se descargan del artefacto `evidencia-pipeline` del enlace anterior.

Durante la preparación se corrigieron dos problemas de portabilidad: una dependencia exclusiva de Windows sin marcador de plataforma y la resolución de un symlink que hacía analizar el Python base en lugar del entorno virtual al generar el SBOM. Los fallos anteriores permanecen visibles en el historial de Actions; no se presentan como la demostración deliberada del control de seguridad.

Verificación del 16 de septiembre de 2026. Si el laboratorio se apaga, la etapa live vuelve a bloquear hasta recuperar el entorno; el resultado registrado no garantiza disponibilidad futura.
