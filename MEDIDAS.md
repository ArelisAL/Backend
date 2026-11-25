# Guía de medidas para confección de prendas
## Mujer, hombre, niños y bebés

Esta guía reúne las medidas que se suelen tomar para confeccionar prendas de vestir, separadas por categoría y por tipo de prenda. Las medidas se toman con una cinta métrica flexible, sobre el cuerpo, sin apretar y en centímetros. No todas las prendas requieren todas las medidas.

> **Uso en el sistema Fran-Costuras.** Este archivo es la fuente del catálogo de medidas del `Backend` (ver `AGENTS.md` §4.4 y DERCAS Anexo A).
> - Cada categoría tiene **una tabla de medidas** (sección A). Es la lista completa de medidas válidas de esa categoría.
> - Cada prenda (sección B) usa **solo** medidas de la tabla de su categoría, escritas con el mismo nombre y el mismo código.
> - Los **códigos** (`snake_case`, sin tildes) son los que se guardan en la base de datos. Códigos de categoría: `MUJER`, `HOMBRE`, `NINO`, `BEBE`.
> - Las medidas marcadas *(agregada)* se añadieron en la versión 2 porque las prendas las pedían y no estaban en la tabla.
> - Las medidas marcadas *(opcional)* se piden solo si el diseño lo requiere; el resto son obligatorias para esa prenda.
> - Todas las medidas se registran en **centímetros**, con hasta un decimal, y deben ser mayores que 0.

## 1. Medidas para prendas de mujer (`MUJER`)

### A. Medidas generales del cuerpo

| N.º | Medida | Código | Cómo se toma |
|---|---|---|---|
| 1 | Contorno de busto | `contorno_busto` | Alrededor de la parte más prominente del busto. |
| 2 | Contorno de busto alto | `contorno_busto_alto` | Por encima del busto, debajo de las axilas. |
| 3 | Contorno de bajo busto | `contorno_bajo_busto` | Debajo del busto. |
| 4 | Contorno de cintura | `contorno_cintura` | En la parte más estrecha del torso o cintura natural. |
| 5 | Contorno de cadera | `contorno_cadera` | Por la parte más prominente de glúteos y cadera. |
| 6 | Contorno de cadera alta | `contorno_cadera_alta` | Alrededor de la parte superior de la cadera. |
| 7 | Ancho de espalda | `ancho_espalda` | De un extremo al otro de la espalda, entre puntos de hombro. |
| 8 | Ancho de pecho | `ancho_pecho` | Entre los puntos de unión de los brazos, por la parte frontal. |
| 9 | Ancho de hombros | `ancho_hombros` | Desde la base de un hombro hasta la del otro. |
| 10 | Largo de talle delantero | `largo_talle_delantero` | Desde el hombro, junto al cuello, hasta la cintura pasando por el busto. |
| 11 | Largo de talle espalda | `largo_talle_espalda` | Desde la base del cuello hasta la cintura por la espalda. |
| 12 | Separación de busto | `separacion_busto` | Distancia entre los dos puntos de busto. |
| 13 | Altura de busto | `altura_busto` | Desde la base del cuello o hombro hasta el punto de busto. |
| 14 | Largo total | `largo_total` | Desde el punto más alto del hombro hasta el largo deseado de la prenda. |
| 15 | Contorno de cuello | `contorno_cuello` | Alrededor de la base del cuello. |
| 16 | Contorno de brazo | `contorno_brazo` | Alrededor de la parte más gruesa del brazo. |
| 17 | Contorno de codo | `contorno_codo` | Alrededor del codo ligeramente flexionado. |
| 18 | Contorno de muñeca | `contorno_muneca` | Alrededor de la muñeca. |
| 19 | Largo de manga | `largo_manga` | Desde el hombro hasta la muñeca, con el brazo ligeramente flexionado. |
| 20 | Largo de brazo | `largo_brazo` | Desde el hombro hasta la muñeca. |
| 21 | Contorno de muslo | `contorno_muslo` | Alrededor de la parte más gruesa del muslo. |
| 22 | Contorno de rodilla | `contorno_rodilla` | Alrededor de la rodilla. |
| 23 | Contorno de pantorrilla | `contorno_pantorrilla` | Alrededor de la parte más gruesa de la pantorrilla. |
| 24 | Contorno de tobillo | `contorno_tobillo` | Alrededor del tobillo. |
| 25 | Largo de entrepierna | `largo_entrepierna` | Desde la entrepierna hasta el tobillo o largo deseado. |
| 26 | Largo exterior de pierna | `largo_exterior_pierna` | Desde la cintura hasta el tobillo por el costado. |
| 27 | Tiro delantero | `tiro_delantero` | Desde la cintura delantera hasta la entrepierna. |
| 28 | Tiro trasero | `tiro_trasero` | Desde la cintura trasera hasta la entrepierna. |
| 29 | Altura de cadera *(agregada)* | `altura_cadera` | Desde la cintura hasta la parte más prominente de la cadera, por el costado. |
| 30 | Largo desde cintura *(agregada)* | `largo_desde_cintura` | Desde la cintura hasta el largo deseado de la falda o el short. |
| 31 | Contorno de bota *(agregada)* | `contorno_bota` | Ancho deseado en la parte inferior del pantalón o short (se toma alrededor del pie o tobillo como referencia). |
| 32 | Largo de abertura *(agregada)* | `largo_abertura` | Largo deseado de la abertura de la falda, desde el borde inferior hacia arriba (solo si lleva). |

### B. Medidas específicas por prenda de mujer

**Blusas y camisas** (`blusas_camisas`)
- Contorno de busto — `contorno_busto`
- Contorno de cintura — `contorno_cintura`
- Ancho de hombros — `ancho_hombros`
- Contorno de cuello — `contorno_cuello`
- Ancho de espalda — `ancho_espalda`
- Largo de talle delantero — `largo_talle_delantero`
- Largo de talle espalda — `largo_talle_espalda`
- Largo total — `largo_total`
- Largo de manga — `largo_manga`
- Contorno de brazo — `contorno_brazo`

**Vestidos** (`vestidos`)
- Contorno de busto — `contorno_busto`
- Contorno de bajo busto — `contorno_bajo_busto`
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Separación de busto — `separacion_busto`
- Altura de busto — `altura_busto`
- Largo de talle delantero — `largo_talle_delantero`
- Largo de talle espalda — `largo_talle_espalda`
- Largo total — `largo_total`
- Largo de manga — `largo_manga`

**Faldas** (`faldas`)
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Contorno de cadera alta — `contorno_cadera_alta`
- Altura de cadera — `altura_cadera`
- Largo desde cintura — `largo_desde_cintura`
- Largo de abertura (opcional) — `largo_abertura`

**Pantalones** (`pantalones`)
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Tiro delantero — `tiro_delantero`
- Tiro trasero — `tiro_trasero`
- Largo de entrepierna — `largo_entrepierna`
- Largo exterior de pierna — `largo_exterior_pierna`
- Contorno de muslo — `contorno_muslo`
- Contorno de rodilla — `contorno_rodilla`
- Contorno de bota — `contorno_bota`

**Chaquetas y blazers** (`chaquetas_blazers`)
- Contorno de busto — `contorno_busto`
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Ancho de hombros — `ancho_hombros`
- Ancho de espalda — `ancho_espalda`
- Largo total — `largo_total`
- Largo de manga — `largo_manga`
- Contorno de brazo — `contorno_brazo`

**Shorts** (`shorts`)
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Tiro delantero — `tiro_delantero`
- Tiro trasero — `tiro_trasero`
- Contorno de muslo — `contorno_muslo`
- Largo de entrepierna — `largo_entrepierna`
- Largo desde cintura — `largo_desde_cintura`

## 2. Medidas para prendas de hombre (`HOMBRE`)

### A. Medidas generales del cuerpo

| N.º | Medida | Código | Cómo se toma |
|---|---|---|---|
| 1 | Contorno de cuello | `contorno_cuello` | Alrededor de la base del cuello. |
| 2 | Contorno de pecho | `contorno_pecho` | Alrededor del pecho, por debajo de las axilas. |
| 3 | Contorno de cintura | `contorno_cintura` | Alrededor de la cintura natural o donde se usa el pantalón. |
| 4 | Contorno de abdomen | `contorno_abdomen` | Alrededor de la parte más prominente del abdomen, si se requiere. |
| 5 | Contorno de cadera | `contorno_cadera` | Alrededor de la parte más amplia de la cadera y glúteos. |
| 6 | Ancho de espalda | `ancho_espalda` | De hombro a hombro por la espalda. |
| 7 | Ancho de hombros | `ancho_hombros` | De extremo a extremo de los hombros. |
| 8 | Largo de talle delantero | `largo_talle_delantero` | Desde el hombro, junto al cuello, hasta la cintura delantera. |
| 9 | Largo de talle espalda | `largo_talle_espalda` | Desde la base del cuello hasta la cintura por la espalda. |
| 10 | Largo de camisa | `largo_camisa` | Desde la base del cuello hasta el largo deseado. |
| 11 | Contorno de brazo | `contorno_brazo` | Alrededor de la parte más gruesa del brazo. |
| 12 | Contorno de codo | `contorno_codo` | Alrededor del codo flexionado. |
| 13 | Contorno de muñeca | `contorno_muneca` | Alrededor de la muñeca. Se usa también para el puño. |
| 14 | Largo de manga | `largo_manga` | Desde el hombro hasta la muñeca. |
| 15 | Largo de brazo | `largo_brazo` | Desde el hombro hasta la muñeca con el brazo flexionado ligeramente. |
| 16 | Contorno de muslo | `contorno_muslo` | Alrededor de la parte más gruesa del muslo. |
| 17 | Contorno de rodilla | `contorno_rodilla` | Alrededor de la rodilla. |
| 18 | Contorno de pantorrilla | `contorno_pantorrilla` | Alrededor de la parte más gruesa de la pantorrilla. |
| 19 | Contorno de tobillo | `contorno_tobillo` | Alrededor del tobillo. |
| 20 | Largo de entrepierna | `largo_entrepierna` | Desde la entrepierna hasta el tobillo. |
| 21 | Largo exterior | `largo_exterior` | Desde la cintura o cadera hasta el tobillo por el costado. |
| 22 | Tiro delantero | `tiro_delantero` | Desde la cintura delantera hasta la entrepierna. |
| 23 | Tiro trasero | `tiro_trasero` | Desde la cintura trasera hasta la entrepierna. |
| 24 | Contorno de bota | `contorno_bota` | Alrededor de la parte inferior del pantalón. |
| 25 | Largo total *(agregada)* | `largo_total` | Desde la base del cuello hasta el largo deseado del saco, sudadera o chaleco. |
| 26 | Largo desde cintura *(agregada)* | `largo_desde_cintura` | Desde la cintura hasta el largo deseado del short o bermuda. |

### B. Medidas específicas por prenda de hombre

**Camisas** (`camisas`)
- Contorno de cuello — `contorno_cuello`
- Contorno de pecho — `contorno_pecho`
- Contorno de cintura — `contorno_cintura`
- Ancho de hombros — `ancho_hombros`
- Ancho de espalda — `ancho_espalda`
- Largo de camisa — `largo_camisa`
- Largo de manga — `largo_manga`
- Contorno de brazo — `contorno_brazo`
- Contorno de muñeca — `contorno_muneca`

**Pantalones** (`pantalones`)
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Contorno de abdomen — `contorno_abdomen`
- Tiro delantero — `tiro_delantero`
- Tiro trasero — `tiro_trasero`
- Contorno de muslo — `contorno_muslo`
- Contorno de rodilla — `contorno_rodilla`
- Largo de entrepierna — `largo_entrepierna`
- Largo exterior — `largo_exterior`
- Contorno de bota — `contorno_bota`

**Sacos y blazers** (`sacos_blazers`)
- Contorno de pecho — `contorno_pecho`
- Contorno de cintura — `contorno_cintura`
- Contorno de abdomen — `contorno_abdomen`
- Contorno de cadera — `contorno_cadera`
- Ancho de hombros — `ancho_hombros`
- Ancho de espalda — `ancho_espalda`
- Largo total — `largo_total`
- Largo de manga — `largo_manga`
- Contorno de brazo — `contorno_brazo`

**Sudaderas** (`sudaderas`)
- Contorno de pecho — `contorno_pecho`
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Ancho de hombros — `ancho_hombros`
- Largo total — `largo_total`
- Largo de manga — `largo_manga`
- Contorno de muñeca — `contorno_muneca`
- Contorno de cuello — `contorno_cuello`

**Shorts y bermudas** (`shorts_bermudas`)
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Contorno de muslo — `contorno_muslo`
- Tiro delantero — `tiro_delantero`
- Tiro trasero — `tiro_trasero`
- Largo de entrepierna — `largo_entrepierna`
- Largo desde cintura — `largo_desde_cintura`
- Contorno de bota — `contorno_bota`

**Chalecos** (`chalecos`)
- Contorno de pecho — `contorno_pecho`
- Contorno de cintura — `contorno_cintura`
- Contorno de abdomen — `contorno_abdomen`
- Ancho de espalda — `ancho_espalda`
- Ancho de hombros — `ancho_hombros`
- Largo de talle delantero — `largo_talle_delantero`
- Largo de talle espalda — `largo_talle_espalda`
- Largo total — `largo_total`

## 3. Medidas para prendas de niños (`NINO`)

### A. Medidas generales del cuerpo

| N.º | Medida | Código | Cómo se toma |
|---|---|---|---|
| 1 | Estatura | `estatura` | Desde la cabeza hasta los pies, de pie y recto. |
| 2 | Contorno de cabeza | `contorno_cabeza` | Alrededor de la parte más amplia de la cabeza, para capuchas y gorros. |
| 3 | Contorno de cuello | `contorno_cuello` | Alrededor de la base del cuello. |
| 4 | Contorno de pecho | `contorno_pecho` | Alrededor del pecho, debajo de las axilas. |
| 5 | Contorno de cintura | `contorno_cintura` | Alrededor de la cintura natural. |
| 6 | Contorno de abdomen | `contorno_abdomen` | Alrededor de la parte más prominente del abdomen. |
| 7 | Contorno de cadera | `contorno_cadera` | Alrededor de la parte más amplia de cadera y glúteos. |
| 8 | Ancho de hombros | `ancho_hombros` | De un extremo del hombro al otro. |
| 9 | Ancho de espalda | `ancho_espalda` | De un lado al otro de la espalda. |
| 10 | Largo de talle delantero | `largo_talle_delantero` | Desde el hombro junto al cuello hasta la cintura. |
| 11 | Largo de talle espalda | `largo_talle_espalda` | Desde la base del cuello hasta la cintura por la espalda. |
| 12 | Largo de prenda | `largo_prenda` | Desde el hombro hasta el largo deseado. |
| 13 | Contorno de brazo | `contorno_brazo` | Alrededor de la parte más gruesa del brazo. |
| 14 | Largo de manga | `largo_manga` | Desde el hombro hasta la muñeca. |
| 15 | Contorno de muñeca | `contorno_muneca` | Alrededor de la muñeca. Se usa también para el puño. |
| 16 | Contorno de muslo | `contorno_muslo` | Alrededor de la parte más gruesa del muslo. Se usa también como contorno de pierna. |
| 17 | Contorno de rodilla | `contorno_rodilla` | Alrededor de la rodilla. |
| 18 | Contorno de pantorrilla | `contorno_pantorrilla` | Alrededor de la parte más gruesa de la pantorrilla. |
| 19 | Contorno de tobillo | `contorno_tobillo` | Alrededor del tobillo. |
| 20 | Tiro delantero | `tiro_delantero` | Desde la cintura delantera hasta la entrepierna. |
| 21 | Tiro trasero | `tiro_trasero` | Desde la cintura trasera hasta la entrepierna. |
| 22 | Largo de entrepierna | `largo_entrepierna` | Desde la entrepierna hasta el tobillo. |
| 23 | Largo exterior | `largo_exterior` | Desde la cintura hasta el tobillo por el costado. |
| 24 | Separación de busto | `separacion_busto` | Solo si se confecciona una prenda para niñas que lo requiera según su desarrollo y diseño. |
| 25 | Altura de cadera *(agregada)* | `altura_cadera` | Desde la cintura hasta la parte más prominente de la cadera, por el costado. |
| 26 | Largo desde cintura *(agregada)* | `largo_desde_cintura` | Desde la cintura hasta el largo deseado de la falda. |
| 27 | Contorno de bota *(agregada)* | `contorno_bota` | Alrededor de la parte inferior del pantalón. |

### B. Medidas específicas por prenda infantil

**Camisetas** (`camisetas`)
- Estatura — `estatura`
- Contorno de pecho — `contorno_pecho`
- Contorno de cintura — `contorno_cintura`
- Ancho de hombros — `ancho_hombros`
- Largo de prenda — `largo_prenda`
- Largo de manga — `largo_manga`
- Contorno de cuello — `contorno_cuello`

**Camisas** (`camisas`)
- Contorno de cuello — `contorno_cuello`
- Contorno de pecho — `contorno_pecho`
- Contorno de cintura — `contorno_cintura`
- Ancho de hombros — `ancho_hombros`
- Ancho de espalda — `ancho_espalda`
- Largo de prenda — `largo_prenda`
- Largo de manga — `largo_manga`
- Contorno de muñeca — `contorno_muneca`

**Vestidos** (`vestidos`)
- Contorno de pecho — `contorno_pecho`
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Ancho de hombros — `ancho_hombros`
- Largo de talle delantero — `largo_talle_delantero`
- Largo de talle espalda — `largo_talle_espalda`
- Largo de prenda — `largo_prenda`
- Largo de manga — `largo_manga`
- Separación de busto (opcional, si el diseño lo requiere) — `separacion_busto`

**Faldas** (`faldas`)
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Altura de cadera — `altura_cadera`
- Largo desde cintura — `largo_desde_cintura`

**Pantalones** (`pantalones`)
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Contorno de muslo — `contorno_muslo`
- Tiro delantero — `tiro_delantero`
- Tiro trasero — `tiro_trasero`
- Largo de entrepierna — `largo_entrepierna`
- Largo exterior — `largo_exterior`
- Contorno de bota — `contorno_bota`

**Chaquetas** (`chaquetas`)
- Contorno de pecho — `contorno_pecho`
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Ancho de hombros — `ancho_hombros`
- Largo de prenda — `largo_prenda`
- Largo de manga — `largo_manga`
- Contorno de brazo — `contorno_brazo`

**Pijamas** (`pijamas`)
- Contorno de pecho — `contorno_pecho`
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Largo de prenda — `largo_prenda`
- Largo de manga — `largo_manga`
- Tiro delantero — `tiro_delantero`
- Tiro trasero — `tiro_trasero`
- Largo de entrepierna — `largo_entrepierna`
- Largo exterior — `largo_exterior`

**Overoles y enterizos** (`overoles_enterizos`)
- Contorno de pecho — `contorno_pecho`
- Contorno de cintura — `contorno_cintura`
- Contorno de cadera — `contorno_cadera`
- Largo de talle delantero — `largo_talle_delantero`
- Largo de talle espalda — `largo_talle_espalda`
- Largo de prenda — `largo_prenda`
- Largo de entrepierna — `largo_entrepierna`
- Largo de manga — `largo_manga`
- Contorno de muslo — `contorno_muslo`

## 4. Medidas para bebés (`BEBE`)

La guía no define prendas específicas para bebé: para cualquier prenda de bebé se usa la tabla completa.

| N.º | Medida | Código | Cómo se toma |
|---|---|---|---|
| 1 | Estatura | `estatura` | Desde la cabeza hasta los pies. |
| 2 | Contorno de cabeza | `contorno_cabeza` | Alrededor de la cabeza. |
| 3 | Contorno de cuello | `contorno_cuello` | En la base del cuello. |
| 4 | Contorno de pecho | `contorno_pecho` | Alrededor del pecho. |
| 5 | Contorno de cintura | `contorno_cintura` | Alrededor de la cintura. |
| 6 | Contorno de cadera | `contorno_cadera` | Alrededor de la cadera y pañal. |
| 7 | Largo de torso | `largo_torso` | Desde el hombro hasta la entrepierna. |
| 8 | Largo total | `largo_total` | Desde el hombro hasta los pies o largo de diseño. |
| 9 | Largo de manga | `largo_manga` | Desde el hombro hasta la mano o muñeca. |
| 10 | Contorno de brazo | `contorno_brazo` | Alrededor de la parte más gruesa del brazo. |
| 11 | Contorno de muñeca | `contorno_muneca` | Alrededor de la muñeca. |
| 12 | Contorno de pierna | `contorno_pierna` | Alrededor de la abertura de la pierna. |
| 13 | Largo de entrepierna | `largo_entrepierna` | Desde la entrepierna hasta el pie o tobillo. |
| 14 | Largo de pie | `largo_pie` | Desde el talón hasta la punta del pie, para prendas que cubren los pies. |

## 5. Resumen rápido de medidas por prenda (referencia general)

> Esta tabla es una **referencia rápida para el taller**. El catálogo del sistema usa las listas exactas de las secciones 1B, 2B, 3B y 4. Las prendas de esta tabla que no aparecen en esas secciones (ropa deportiva, ropa interior, abrigo) **no están en el catálogo**; si se necesitan, primero hay que agregarlas aquí con sus medidas.

| Prenda | Medidas necesarias |
|---|---|
| Blusa | Busto, cintura, hombros, espalda, talle, cuello, manga, largo. |
| Camisa | Cuello, pecho, cintura, espalda, hombros, manga, puño, largo. |
| Vestido | Busto, bajo busto, cintura, cadera, talle, hombros, largo, manga. |
| Falda | Cintura, cadera, altura de cadera, largo. |
| Pantalón | Cintura, cadera, muslo, tiro delantero, tiro trasero, entrepierna, largo, bota. |
| Short | Cintura, cadera, muslo, tiro, entrepierna, largo, bota. |
| Chaqueta | Pecho o busto, cintura, cadera, hombros, espalda, manga, largo, brazo. |
| Saco | Pecho, abdomen, cintura, cadera, espalda, hombros, manga, largo. |
| Chaleco | Pecho o busto, cintura, cadera, espalda, hombros, largo. |
| Enterizo | Busto o pecho, cintura, cadera, talle, tiro, entrepierna, largo total, manga. |
| Pijama | Pecho o busto, cintura, cadera, manga, largo de camiseta, tiro, entrepierna, largo de pantalón. |
| Ropa deportiva | Pecho o busto, cintura, cadera, muslo, largo, manga, entrepierna. |
| Ropa interior | Cintura, cadera, pecho o busto, tiro, contorno de pierna, según el modelo. |
| Abrigo | Pecho o busto, cintura, cadera, hombros, espalda, largo, manga, contorno de brazo. |
| Overol | Pecho, cintura, cadera, talle, tiro, entrepierna, largo total, manga. |

## 6. Recomendaciones para tomar medidas

- Utilizar una cinta métrica flexible.
- No apretar la cinta contra el cuerpo.
- Tomar las medidas con ropa ligera.
- Mantener la cinta recta y nivelada al medir contornos.
- Registrar las medidas en centímetros.
- No confundir medidas del cuerpo con medidas finales de la prenda.
- Añadir holgura de acuerdo con el tipo de tela, diseño y comodidad requerida.
- En telas elásticas, ajustar la holgura según el nivel de elasticidad.
- En niños, considerar la comodidad y el crecimiento, sin alterar excesivamente el ajuste de la prenda.

**Nota:** Esta guía es una referencia general. Las medidas y holguras exactas pueden variar según el sistema de patronaje, el diseño, el tipo de tela y el ajuste deseado.

## 7. Cambios de la versión 2

| Categoría | Cambio | Motivo |
|---|---|---|
| Todas | Se agregó la columna **Código** y los códigos de categoría y de prenda | El sistema guarda las medidas con un código fijo |
| Todas | Las listas por prenda usan el nombre exacto de la tabla (ej. «Busto» → «Contorno de busto», «Hombros» → «Ancho de hombros», «Talle» → «Largo de talle delantero» y «Largo de talle espalda») | Evitar ambigüedades al cargar el catálogo |
| Mujer | Se agregaron: Altura de cadera, Largo desde cintura, Contorno de bota, Largo de abertura | Las pedían faldas, pantalones y shorts y no estaban en la tabla |
| Mujer | «Largo de blusa / vestido / chaqueta» → Largo total; «Largo de falda / shorts» → Largo desde cintura; «Contorno de manga» → Contorno de brazo; «Entrepierna» → Largo de entrepierna; «Largo exterior» → Largo exterior de pierna | Unificar con la tabla |
| Hombre | Se agregaron: Largo total, Largo desde cintura | Las pedían sacos, sudaderas, chalecos y shorts |
| Hombre | «Puño» → Contorno de muñeca; «Largo de saco / largo» → Largo total; «Largo delantero / espalda» del chaleco → Largo de talle delantero / espalda | Unificar con la tabla |
| Niños | Se agregaron: Altura de cadera, Largo desde cintura, Contorno de bota | Las pedían faldas y pantalones |
| Niños | «Puño» → Contorno de muñeca; «Contorno de pierna» → Contorno de muslo; «Largo / largo de vestido / largo total» → Largo de prenda; «Tiro» → Tiro delantero y Tiro trasero | Unificar con la tabla |
| Bebés | Sin cambios; se aclara que se usa la tabla completa | La guía no define prendas de bebé |
