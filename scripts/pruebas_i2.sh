#!/usr/bin/env bash

set -u

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env"
    set +a
fi

ADMIN_PASSWORD="${E2E_ADMIN_PASSWORD:-}"
OPERADOR1_PASSWORD="${E2E_OPERADOR1_PASSWORD:-}"
OPERADOR2_PASSWORD="${E2E_OPERADOR2_PASSWORD:-}"
OPERADOR3_PASSWORD="${E2E_OPERADOR3_PASSWORD:-}"

for variable in ADMIN_PASSWORD OPERADOR1_PASSWORD OPERADOR2_PASSWORD OPERADOR3_PASSWORD DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD; do
    if [ -z "${!variable:-}" ]; then
        echo "[ERROR] Falta configurar $variable o su variable correspondiente en .env."
        exit 1
    fi
done

if [ -x "$PROJECT_ROOT/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/Scripts/python.exe"
else
    PYTHON_BIN="python"
fi

PASS=0
FAIL=0
HTTP_STATUS=""
HTTP_BODY=""
ADMIN_TOKEN=""
OPERADOR1_TOKEN=""
OPERADOR2_TOKEN=""
TEST_OPERADOR_ID=""
TEST_ADMIN_ID=""

mostrar_resultado() {
    local id="$1"
    local resultado="$2"
    local detalle="$3"

    if [ "$resultado" = "PASS" ]; then
        PASS=$((PASS + 1))
        echo "[PASS] $id - $detalle"
    else
        FAIL=$((FAIL + 1))
        echo "[FAIL] $id - $detalle"
    fi
}

request() {
    local method="$1"
    local path="$2"
    local token="${3:-}"
    local body="${4:-}"
    local respuesta
    local args=(-sS -w $'\n%{http_code}' -X "$method" "$BASE_URL$path")

    if [ -n "$token" ]; then
        args+=(-H "Authorization: Bearer $token")
    fi

    if [ -n "$body" ]; then
        args+=(-H "Content-Type: application/json" -d "$body")
    fi

    respuesta="$(curl "${args[@]}" 2>&1)"
    HTTP_STATUS="${respuesta##*$'\n'}"
    HTTP_BODY="${respuesta%$'\n'*}"
}

json_get() {
    local json="$1"
    local path="$2"
    JSON_INPUT="$json" JSON_PATH="$path" "$PYTHON_BIN" -c '
import json, os
try:
    data = json.loads(os.environ["JSON_INPUT"])
    for part in os.environ["JSON_PATH"].split("."):
        if isinstance(data, list):
            data = data[int(part)]
        else:
            data = data.get(part)
    if data is True:
        print("true")
    elif data is False:
        print("false")
    elif data is None:
        print("")
    else:
        print(data)
except Exception:
    print("")
'
}

json_contiene_celda() {
    local json="$1"
    local codigo="$2"
    JSON_INPUT="$json" CODIGO="$codigo" "$PYTHON_BIN" -c '
import json, os
try:
    data = json.loads(os.environ["JSON_INPUT"])
    celdas = data.get("celdas", [])
    print("true" if any(c.get("codigo") == os.environ["CODIGO"] for c in celdas) else "false")
except Exception:
    print("false")
'
}

db_scalar() {
    local consulta="$1"
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -tA \
        -c "$consulta" 2>/dev/null | tr -d '\r'
}

reset_db() {
    echo "[INFO] Reiniciando base de pruebas..."

    if ! PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -v ON_ERROR_STOP=1 \
        -f "$PROJECT_ROOT/sql/autos_colombia.sql" >/dev/null 2>&1; then
        echo "[ERROR] No fue posible recrear la base con autos_colombia.sql."
        exit 1
    fi

    if ! "$PYTHON_BIN" "$PROJECT_ROOT/scripts/seed_usuarios.py" >/dev/null 2>&1; then
        echo "[ERROR] No fue posible ejecutar seed_usuarios.py."
        exit 1
    fi

    echo "[INFO] Base preparada."
    echo
}

login_token() {
    local usuario="$1"
    local password="$2"
    request "POST" "/api/auth/login" "" "{\"usuario\":\"$usuario\",\"password\":\"$password\"}"
    if [ "$HTTP_STATUS" = "200" ]; then
        json_get "$HTTP_BODY" "token"
    else
        printf ''
    fi
}

cleanup_final() {
    echo
    echo "[INFO] Restaurando base a estado inicial..."
    if PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -v ON_ERROR_STOP=1 \
        -f "$PROJECT_ROOT/sql/autos_colombia.sql" >/dev/null 2>&1 \
        && "$PYTHON_BIN" "$PROJECT_ROOT/scripts/seed_usuarios.py" >/dev/null 2>&1; then
        echo "[INFO] Base restaurada correctamente."
    else
        mostrar_resultado "CLEANUP" "FAIL" "No fue posible restaurar la base al estado inicial."
    fi
}

echo "=========================================="
echo "AUTOS COLOMBIA - PRUEBAS BACKEND I2"
echo "Base URL: $BASE_URL"
echo "=========================================="
echo

echo "IMPORTANTE: este script recrea la base al inicio y al final."
echo

reset_db

# US-01 - Login administrador
request "POST" "/api/auth/login" "" "{\"usuario\":\"admin\",\"password\":\"$ADMIN_PASSWORD\"}"
ADMIN_TOKEN="$(json_get "$HTTP_BODY" "token")"
if [ "$HTTP_STATUS" = "200" ] \
    && [ -n "$ADMIN_TOKEN" ] \
    && [ "$(json_get "$HTTP_BODY" "usuario.rol")" = "ADMINISTRADOR" ]; then
    mostrar_resultado "US-01" "PASS" "Login de administrador: 200, token y rol ADMINISTRADOR."
else
    mostrar_resultado "US-01" "FAIL" "Login de administrador no devolvió la respuesta esperada."
fi

# US-02 - Login operador
request "POST" "/api/auth/login" "" "{\"usuario\":\"operador1\",\"password\":\"$OPERADOR1_PASSWORD\"}"
OPERADOR1_TOKEN="$(json_get "$HTTP_BODY" "token")"
if [ "$HTTP_STATUS" = "200" ] \
    && [ -n "$OPERADOR1_TOKEN" ] \
    && [ "$(json_get "$HTTP_BODY" "usuario.rol")" = "OPERADOR" ]; then
    mostrar_resultado "US-02" "PASS" "Login de operador: 200, token y rol OPERADOR."
else
    mostrar_resultado "US-02" "FAIL" "Login de operador no devolvió la respuesta esperada."
fi

# US-03 - Credenciales incorrectas y campos vacíos
request "POST" "/api/auth/login" "" '{"usuario":"operador1","password":"ClaveIncorrecta999"}'
us03_bad="$HTTP_STATUS"
us03_bad_body="$HTTP_BODY"
request "POST" "/api/auth/login" "" '{"usuario":"","password":""}'
us03_empty="$HTTP_STATUS"
if [ "$us03_bad" = "401" ] \
    && echo "$us03_bad_body" | grep -q 'incorrectos\.' \
    && [ "$us03_empty" = "422" ]; then
    mostrar_resultado "US-03" "PASS" "Credenciales incorrectas: 401; campos vacíos: 422."
else
    mostrar_resultado "US-03" "FAIL" "Falló la validación de credenciales incorrectas o campos vacíos."
fi

# US-04 - Dos sesiones simultáneas y operador tomado del token
request "POST" "/api/auth/login" "" "{\"usuario\":\"operador2\",\"password\":\"$OPERADOR2_PASSWORD\"}"
OPERADOR2_TOKEN="$(json_get "$HTTP_BODY" "token")"
request "GET" "/api/auth/me" "$OPERADOR1_TOKEN"
us04_me1="$HTTP_STATUS"
request "GET" "/api/auth/me" "$OPERADOR2_TOKEN"
us04_me2="$HTTP_STATUS"
request "POST" "/api/entradas" "$OPERADOR1_TOKEN" '{"placa":"ABC123","codigo_celda":"C01"}'
us04_e1="$HTTP_STATUS"
request "POST" "/api/entradas" "$OPERADOR2_TOKEN" '{"placa":"GHI789","codigo_celda":"C02"}'
us04_e2="$HTTP_STATUS"
us04_db1="$(db_scalar "SELECT e.id_operador_entrada FROM estancia e JOIN vehiculo v ON v.id_vehiculo=e.id_vehiculo WHERE v.placa='ABC123' AND e.estado='ACTIVA' ORDER BY e.id_estancia DESC LIMIT 1;")"
us04_db2="$(db_scalar "SELECT e.id_operador_entrada FROM estancia e JOIN vehiculo v ON v.id_vehiculo=e.id_vehiculo WHERE v.placa='GHI789' AND e.estado='ACTIVA' ORDER BY e.id_estancia DESC LIMIT 1;")"
request "POST" "/api/salidas" "$OPERADOR1_TOKEN" '{"placa":"ABC123"}'
us04_s1="$HTTP_STATUS"
request "POST" "/api/salidas" "$OPERADOR2_TOKEN" '{"placa":"GHI789"}'
us04_s2="$HTTP_STATUS"
if [ "$us04_me1" = "200" ] && [ "$us04_me2" = "200" ] \
    && [ "$us04_e1" = "201" ] && [ "$us04_e2" = "201" ] \
    && [ "$us04_db1" = "1" ] && [ "$us04_db2" = "2" ] \
    && [ "$us04_s1" = "200" ] && [ "$us04_s2" = "200" ]; then
    mostrar_resultado "US-04" "PASS" "Dos sesiones simultáneas funcionan y cada estancia toma su operador del token."
else
    mostrar_resultado "US-04" "FAIL" "Falló la concurrencia de sesiones o la asociación automática del operador."
fi

# US-05 - Sesión vencida
request "POST" "/api/auth/login" "" "{\"usuario\":\"operador3\",\"password\":\"$OPERADOR3_PASSWORD\"}"
OPERADOR3_TOKEN="$(json_get "$HTTP_BODY" "token")"
db_scalar "UPDATE sesion SET expira=CURRENT_TIMESTAMP - INTERVAL '1 minute' WHERE id_operador=3 AND revocada=FALSE;" >/dev/null
request "GET" "/api/auth/me" "$OPERADOR3_TOKEN"
if [ "$HTTP_STATUS" = "401" ]; then
    mostrar_resultado "US-05" "PASS" "Una sesión vencida es rechazada con 401."
else
    mostrar_resultado "US-05" "FAIL" "La sesión vencida no fue rechazada con 401."
fi

# US-06 - Logout efectivo
request "POST" "/api/auth/logout" "$OPERADOR2_TOKEN"
us06_logout="$HTTP_STATUS"
request "GET" "/api/auth/me" "$OPERADOR2_TOKEN"
us06_reuso="$HTTP_STATUS"
if [ "$us06_logout" = "200" ] && [ "$us06_reuso" = "401" ]; then
    mostrar_resultado "US-06" "PASS" "Logout revoca el token y su reutilización devuelve 401."
else
    mostrar_resultado "US-06" "FAIL" "El logout no revocó correctamente la sesión."
fi

# US-07 - Crear operador y administrador
request "POST" "/api/usuarios" "$ADMIN_TOKEN" "{\"nombre\":\"Operador Prueba\",\"usuario\":\"pruebaoperador\",\"password\":\"$ADMIN_PASSWORD\",\"rol\":\"OPERADOR\"}"
us07_op_status="$HTTP_STATUS"
us07_op_body="$HTTP_BODY"
TEST_OPERADOR_ID="$(json_get "$HTTP_BODY" "usuario.id_operador")"
request "POST" "/api/usuarios" "$ADMIN_TOKEN" "{\"nombre\":\"Administrador Prueba\",\"usuario\":\"pruebaadmin\",\"password\":\"$ADMIN_PASSWORD\",\"rol\":\"ADMINISTRADOR\"}"
us07_ad_status="$HTTP_STATUS"
us07_ad_body="$HTTP_BODY"
TEST_ADMIN_ID="$(json_get "$HTTP_BODY" "usuario.id_operador")"
if [ "$us07_op_status" = "201" ] && [ "$us07_ad_status" = "201" ] \
    && [ -n "$TEST_OPERADOR_ID" ] && [ -n "$TEST_ADMIN_ID" ] \
    && ! echo "$us07_op_body$us07_ad_body" | grep -Eq '"password(_hash)?"'; then
    mostrar_resultado "US-07" "PASS" "Se crean operador y administrador con 201 sin exponer contraseña ni hash."
else
    mostrar_resultado "US-07" "FAIL" "Falló la creación de usuarios o se expuso información de contraseña."
fi

# US-08 - Usuario duplicado
request "POST" "/api/usuarios" "$ADMIN_TOKEN" "{\"nombre\":\"Duplicado\",\"usuario\":\" pruebaoperador \",\"password\":\"$ADMIN_PASSWORD\",\"rol\":\"OPERADOR\"}"
if [ "$HTTP_STATUS" = "409" ]; then
    mostrar_resultado "US-08" "PASS" "Usuario duplicado normalizado es rechazado con 409."
else
    mostrar_resultado "US-08" "FAIL" "Usuario duplicado no fue rechazado con 409."
fi

# US-09 - Datos obligatorios y rol inválido
request "POST" "/api/usuarios" "$ADMIN_TOKEN" '{"nombre":"","usuario":"x","password":"12345678","rol":"OPERADOR"}'
us09_empty="$HTTP_STATUS"
request "POST" "/api/usuarios" "$ADMIN_TOKEN" '{"nombre":"Rol Invalido","usuario":"rolinvalido","password":"12345678","rol":"SUPERVISOR"}'
us09_role="$HTTP_STATUS"
if [ "$us09_empty" = "422" ] && [ "$us09_role" = "422" ]; then
    mostrar_resultado "US-09" "PASS" "Datos obligatorios y rol inválido son rechazados con 422."
else
    mostrar_resultado "US-09" "FAIL" "Alguna validación de usuario no devolvió 422."
fi

# US-10 - Modificar usuario y mantener login inmutable
request "PUT" "/api/usuarios/$TEST_OPERADOR_ID" "$ADMIN_TOKEN" '{"nombre":"Operador Prueba Modificado"}'
us10_update="$HTTP_STATUS"
us10_username="$(json_get "$HTTP_BODY" "usuario.usuario")"
request "PUT" "/api/usuarios/$TEST_OPERADOR_ID" "$ADMIN_TOKEN" '{"usuario":"otro_login"}'
us10_login_change="$HTTP_STATUS"
if [ "$us10_update" = "200" ] && [ "$us10_username" = "pruebaoperador" ] && [ "$us10_login_change" = "422" ]; then
    mostrar_resultado "US-10" "PASS" "La modificación persiste y el nombre de usuario de acceso no puede cambiarse."
else
    mostrar_resultado "US-10" "FAIL" "Falló la modificación o la inmutabilidad del login."
fi

# US-11 - Retirar operador, revocar sesión y conservar historial
request "POST" "/api/auth/login" "" "{\"usuario\":\"pruebaoperador\",\"password\":\"$ADMIN_PASSWORD\"}"
TEST_OPERADOR_TOKEN="$(json_get "$HTTP_BODY" "token")"
request "POST" "/api/entradas" "$TEST_OPERADOR_TOKEN" '{"placa":"ABC123","codigo_celda":"C01"}'
us11_entry="$HTTP_STATUS"
request "POST" "/api/salidas" "$TEST_OPERADOR_TOKEN" '{"placa":"ABC123"}'
us11_exit="$HTTP_STATUS"
us11_hist_before="$(db_scalar "SELECT COUNT(*) FROM estancia WHERE id_operador_entrada=$TEST_OPERADOR_ID OR id_operador_salida=$TEST_OPERADOR_ID;")"
request "PATCH" "/api/usuarios/$TEST_OPERADOR_ID/estado" "$ADMIN_TOKEN" '{"estado":"INACTIVO"}'
us11_inactive="$HTTP_STATUS"
request "GET" "/api/auth/me" "$TEST_OPERADOR_TOKEN"
us11_old_token="$HTTP_STATUS"
request "POST" "/api/auth/login" "" "{\"usuario\":\"pruebaoperador\",\"password\":\"$ADMIN_PASSWORD\"}"
us11_login="$HTTP_STATUS"
us11_hist_after="$(db_scalar "SELECT COUNT(*) FROM estancia WHERE id_operador_entrada=$TEST_OPERADOR_ID OR id_operador_salida=$TEST_OPERADOR_ID;")"
if [ "$us11_entry" = "201" ] && [ "$us11_exit" = "200" ] \
    && [ "$us11_inactive" = "200" ] && [ "$us11_old_token" = "401" ] \
    && [ "$us11_login" = "401" ] && [ "$us11_hist_before" = "$us11_hist_after" ] \
    && [ "${us11_hist_after:-0}" -gt 0 ]; then
    mostrar_resultado "US-11" "PASS" "Inactivar revoca sesiones y login, conservando el historial de estancias."
else
    mostrar_resultado "US-11" "FAIL" "Falló la inactivación, revocación o conservación del historial."
fi

# US-12 - Último administrador y auto-inactivación
request "PATCH" "/api/usuarios/$TEST_ADMIN_ID/estado" "$ADMIN_TOKEN" '{"estado":"INACTIVO"}'
us12_aux="$HTTP_STATUS"
request "PATCH" "/api/usuarios/4/estado" "$ADMIN_TOKEN" '{"estado":"INACTIVO"}'
us12_self="$HTTP_STATUS"
request "PUT" "/api/usuarios/4" "$ADMIN_TOKEN" '{"rol":"OPERADOR"}'
us12_last="$HTTP_STATUS"
if [ "$us12_aux" = "200" ] && [ "$us12_self" = "409" ] && [ "$us12_last" = "409" ]; then
    mostrar_resultado "US-12" "PASS" "Auto-inactivación y dejar al sistema sin administrador activo son rechazados con 409."
else
    mostrar_resultado "US-12" "FAIL" "Falló alguna regla de protección del administrador."
fi

# US-13 - Protección de contraseña
request "GET" "/api/usuarios" "$ADMIN_TOKEN"
us13_api="$HTTP_STATUS"
us13_hash="$(db_scalar "SELECT password_hash FROM operador WHERE usuario='pruebaoperador';")"
if [ "$us13_api" = "200" ] \
    && ! echo "$HTTP_BODY" | grep -Eq '"password(_hash)?"' \
    && [ -n "$us13_hash" ] \
    && [ "$us13_hash" != "$ADMIN_PASSWORD" ]; then
    mostrar_resultado "US-13" "PASS" "La API no expone contraseña/hash y la base almacena un hash, no texto plano."
else
    mostrar_resultado "US-13" "FAIL" "La protección de contraseña no cumple lo esperado."
fi

# PE-01 - Solicitudes sin autenticación
request "GET" "/api/usuarios"
pe01_users="$HTTP_STATUS"
request "POST" "/api/entradas" "" '{"placa":"ABC123","codigo_celda":"C01"}'
pe01_entry="$HTTP_STATUS"
request "PATCH" "/api/celdas/C07/deshabilitar" "" '{}'
pe01_cell="$HTTP_STATUS"
if [ "$pe01_users" = "401" ] && [ "$pe01_entry" = "401" ] && [ "$pe01_cell" = "401" ]; then
    mostrar_resultado "PE-01" "PASS" "Solicitudes protegidas sin token son rechazadas con 401."
else
    mostrar_resultado "PE-01" "FAIL" "Alguna ruta protegida permitió acceso sin token."
fi

# PE-02 - Operador intenta administrar usuarios
request "GET" "/api/usuarios" "$OPERADOR1_TOKEN"
pe02_get="$HTTP_STATUS"
request "POST" "/api/usuarios" "$OPERADOR1_TOKEN" '{"nombre":"No Permitido","usuario":"nopermitido","password":"12345678","rol":"OPERADOR"}'
pe02_post="$HTTP_STATUS"
if [ "$pe02_get" = "403" ] && [ "$pe02_post" = "403" ]; then
    mostrar_resultado "PE-02" "PASS" "OPERADOR no puede consultar ni crear usuarios: 403."
else
    mostrar_resultado "PE-02" "FAIL" "El OPERADOR obtuvo acceso indebido a gestión de usuarios."
fi

# PE-03 - Operador intenta modificar clientes, vehículos o celdas
request "PUT" "/api/clientes/1" "$OPERADOR1_TOKEN" '{"nombre":"Cambio No Permitido"}'
pe03_client="$HTTP_STATUS"
request "PUT" "/api/vehiculos/ABC123" "$OPERADOR1_TOKEN" '{"color":"Negro"}'
pe03_vehicle="$HTTP_STATUS"
request "PATCH" "/api/celdas/C07/deshabilitar" "$OPERADOR1_TOKEN" '{}'
pe03_cell="$HTTP_STATUS"
if [ "$pe03_client" = "403" ] && [ "$pe03_vehicle" = "403" ] && [ "$pe03_cell" = "403" ]; then
    mostrar_resultado "PE-03" "PASS" "OPERADOR no puede modificar clientes, vehículos ni administrar celdas."
else
    mostrar_resultado "PE-03" "FAIL" "El OPERADOR obtuvo permisos administrativos indebidos."
fi

# PE-04 - Administrador hereda operaciones del operador
request "POST" "/api/entradas" "$ADMIN_TOKEN" '{"placa":"GHI789","codigo_celda":"C02"}'
pe04_entry="$HTTP_STATUS"
pe04_entry_operator="$(json_get "$HTTP_BODY" "estancia.operador.id_operador")"
request "POST" "/api/salidas" "$ADMIN_TOKEN" '{"placa":"GHI789"}'
pe04_exit="$HTTP_STATUS"
pe04_exit_operator="$(json_get "$HTTP_BODY" "estancia.operador_salida.id_operador")"
if [ "$pe04_entry" = "201" ] && [ "$pe04_entry_operator" = "4" ] \
    && [ "$pe04_exit" = "200" ] && [ "$pe04_exit_operator" = "4" ]; then
    mostrar_resultado "PE-04" "PASS" "ADMINISTRADOR registra entrada/salida y queda asociado desde su sesión."
else
    mostrar_resultado "PE-04" "FAIL" "El ADMINISTRADOR no heredó correctamente entrada/salida."
fi

# CV-01 - Registrar cliente y vehículo; reutilizar documento existente
request "POST" "/api/registros" "$OPERADOR1_TOKEN" '{"documento":"DOCV01","nombre":"Cliente CV","placa":"CV001","marca":"Mazda","color":"Azul","tipo_vehiculo":"AUTOMOVIL"}'
cv01_first="$HTTP_STATUS"
cv01_client_id="$(json_get "$HTTP_BODY" "cliente.id_cliente")"
cv01_monthly="$(json_get "$HTTP_BODY" "vehiculo.estado_mensualidad")"
request "POST" "/api/registros" "$OPERADOR1_TOKEN" '{"documento":"DOCV01","nombre":"Nombre Ignorado","placa":"CV002","marca":"Kia","color":"Gris","tipo_vehiculo":"CAMIONETA"}'
cv01_second="$HTTP_STATUS"
cv01_client_id2="$(json_get "$HTTP_BODY" "cliente.id_cliente")"
if [ "$cv01_first" = "201" ] && [ "$cv01_second" = "201" ] \
    && [ "$cv01_monthly" = "ACTIVA" ] \
    && [ -n "$cv01_client_id" ] && [ "$cv01_client_id" = "$cv01_client_id2" ]; then
    mostrar_resultado "CV-01" "PASS" "Registro transaccional crea vehículo ACTIVO y reutiliza cliente por documento."
else
    mostrar_resultado "CV-01" "FAIL" "Falló el registro cliente/vehículo o la reutilización del documento."
fi

# CV-02 - Placa duplicada, datos inválidos y sin parciales
request "POST" "/api/registros" "$OPERADOR1_TOKEN" '{"documento":"DOCPARCIAL","nombre":"No Debe Persistir","placa":"CV001","marca":"Ford","color":"Rojo","tipo_vehiculo":"AUTOMOVIL"}'
cv02_duplicate="$HTTP_STATUS"
cv02_partial_count="$(db_scalar "SELECT COUNT(*) FROM cliente WHERE documento='DOCPARCIAL';")"
request "POST" "/api/registros" "$OPERADOR1_TOKEN" '{"documento":"DOC-INVALIDO","nombre":"Invalido","placa":"BAD001","marca":"Ford","color":"Rojo","tipo_vehiculo":"AUTOMOVIL"}'
cv02_invalid="$HTTP_STATUS"
cv02_invalid_client="$(db_scalar "SELECT COUNT(*) FROM cliente WHERE documento='DOC-INVALIDO';")"
cv02_invalid_vehicle="$(db_scalar "SELECT COUNT(*) FROM vehiculo WHERE placa='BAD001';")"
if [ "$cv02_duplicate" = "409" ] && [ "$cv02_partial_count" = "0" ] \
    && [ "$cv02_invalid" = "422" ] && [ "$cv02_invalid_client" = "0" ] \
    && [ "$cv02_invalid_vehicle" = "0" ]; then
    mostrar_resultado "CV-02" "PASS" "Duplicados/datos inválidos son rechazados sin registros parciales."
else
    mostrar_resultado "CV-02" "FAIL" "Falló el rechazo o quedaron datos parciales."
fi

# CV-03 - Administrador modifica cliente/vehículo; tipo bloqueado con estancia activa
request "PUT" "/api/clientes/$cv01_client_id" "$ADMIN_TOKEN" '{"nombre":"Cliente CV Modificado"}'
cv03_client="$HTTP_STATUS"
request "PUT" "/api/vehiculos/CV001" "$ADMIN_TOKEN" '{"color":"Negro"}'
cv03_vehicle="$HTTP_STATUS"
request "POST" "/api/entradas" "$OPERADOR1_TOKEN" '{"placa":"CV001","codigo_celda":"C03"}'
cv03_entry="$HTTP_STATUS"
request "PUT" "/api/vehiculos/CV001" "$ADMIN_TOKEN" '{"tipo_vehiculo":"MOTO"}'
cv03_type="$HTTP_STATUS"
request "POST" "/api/salidas" "$OPERADOR1_TOKEN" '{"placa":"CV001"}'
cv03_exit="$HTTP_STATUS"
if [ "$cv03_client" = "200" ] && [ "$cv03_vehicle" = "200" ] \
    && [ "$cv03_entry" = "201" ] && [ "$cv03_type" = "409" ] \
    && [ "$cv03_exit" = "200" ]; then
    mostrar_resultado "CV-03" "PASS" "ADMIN modifica datos; cambio de tipo con estancia activa es rechazado con 409."
else
    mostrar_resultado "CV-03" "FAIL" "Falló la modificación o la regla de tipo con estancia activa."
fi

# CE-01 - Listar y filtrar 80 celdas
request "GET" "/api/celdas" "$ADMIN_TOKEN"
ce01_all="$HTTP_STATUS"
ce01_count="$(json_get "$HTTP_BODY" "cantidad")"
request "GET" "/api/celdas?tipo=MOTO" "$ADMIN_TOKEN"
ce01_moto="$HTTP_STATUS"
ce01_moto_count="$(json_get "$HTTP_BODY" "cantidad")"
if [ "$ce01_all" = "200" ] && [ "$ce01_count" = "80" ] \
    && [ "$ce01_moto" = "200" ] && [ "$ce01_moto_count" = "10" ]; then
    mostrar_resultado "CE-01" "PASS" "Se listan 80 celdas y el filtro MOTO devuelve 10."
else
    mostrar_resultado "CE-01" "FAIL" "Listado o filtros de celdas incorrectos."
fi

# CE-02 - Deshabilitar celda disponible
request "PATCH" "/api/celdas/C07/deshabilitar" "$ADMIN_TOKEN" '{}'
ce02_status="$HTTP_STATUS"
ce02_state="$(json_get "$HTTP_BODY" "celda.estado")"
if [ "$ce02_status" = "200" ] && [ "$ce02_state" = "FUERA_DE_SERVICIO" ]; then
    mostrar_resultado "CE-02" "PASS" "Celda disponible pasa a FUERA_DE_SERVICIO."
else
    mostrar_resultado "CE-02" "FAIL" "No fue posible deshabilitar correctamente una celda libre."
fi

# CE-03 - No deshabilitar celda ocupada
request "POST" "/api/entradas" "$OPERADOR1_TOKEN" '{"placa":"ABC123","codigo_celda":"C03"}'
ce03_entry="$HTTP_STATUS"
request "PATCH" "/api/celdas/C03/deshabilitar" "$ADMIN_TOKEN" '{}'
ce03_disable="$HTTP_STATUS"
ce03_state="$(db_scalar "SELECT estado FROM celda WHERE codigo='C03';")"
request "POST" "/api/salidas" "$OPERADOR1_TOKEN" '{"placa":"ABC123"}'
ce03_exit="$HTTP_STATUS"
if [ "$ce03_entry" = "201" ] && [ "$ce03_disable" = "409" ] \
    && [ "$ce03_state" = "OCUPADA" ] && [ "$ce03_exit" = "200" ]; then
    mostrar_resultado "CE-03" "PASS" "Celda ocupada no se deshabilita y la estancia permanece coherente."
else
    mostrar_resultado "CE-03" "FAIL" "Falló la protección de una celda ocupada."
fi

# CE-04 - Celda fuera de servicio excluida del ingreso
request "GET" "/api/celdas/disponibles?tipo_vehiculo=AUTOMOVIL" "$OPERADOR1_TOKEN"
ce04_list="$HTTP_STATUS"
ce04_contains="$(json_contiene_celda "$HTTP_BODY" "C07")"
request "POST" "/api/entradas" "$OPERADOR1_TOKEN" '{"placa":"DEF456","codigo_celda":"C07"}'
ce04_entry="$HTTP_STATUS"
request "GET" "/api/parqueadero/estado" "$OPERADOR1_TOKEN"
ce04_summary="$HTTP_STATUS"
ce04_out="$(json_get "$HTTP_BODY" "celdas.fuera_de_servicio")"
if [ "$ce04_list" = "200" ] && [ "$ce04_contains" = "false" ] \
    && [ "$ce04_entry" = "400" ] && [ "$ce04_summary" = "200" ] \
    && [ "$ce04_out" = "1" ]; then
    mostrar_resultado "CE-04" "PASS" "FUERA_DE_SERVICIO no aparece disponible, no admite entrada y cuenta en el resumen."
else
    mostrar_resultado "CE-04" "FAIL" "Falló la exclusión de una celda fuera de servicio."
fi

# CE-05 - Habilitar solo una celda fuera de servicio
request "PATCH" "/api/celdas/C07/habilitar" "$ADMIN_TOKEN" '{}'
ce05_enable="$HTTP_STATUS"
ce05_state="$(json_get "$HTTP_BODY" "celda.estado")"
request "PATCH" "/api/celdas/C07/habilitar" "$ADMIN_TOKEN" '{}'
ce05_repeat="$HTTP_STATUS"
request "GET" "/api/celdas/disponibles?tipo_vehiculo=AUTOMOVIL" "$OPERADOR1_TOKEN"
ce05_contains="$(json_contiene_celda "$HTTP_BODY" "C07")"
if [ "$ce05_enable" = "200" ] && [ "$ce05_state" = "DISPONIBLE" ] \
    && [ "$ce05_repeat" = "409" ] && [ "$ce05_contains" = "true" ]; then
    mostrar_resultado "CE-05" "PASS" "Habilitar restaura DISPONIBLE; repetir habilitación devuelve 409."
else
    mostrar_resultado "CE-05" "FAIL" "Falló la transición de habilitación de la celda."
fi

# CE-06 - Concurrencia: entrada vs deshabilitación sobre C08
TMP_DIR="$(mktemp -d)"
(
    curl -sS -o "$TMP_DIR/entrada.body" -w '%{http_code}' \
        -X POST "$BASE_URL/api/entradas" \
        -H "Authorization: Bearer $OPERADOR1_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"placa":"DEF456","codigo_celda":"C08"}' \
        > "$TMP_DIR/entrada.code"
) &
PID_ENTRADA=$!
(
    curl -sS -o "$TMP_DIR/celda.body" -w '%{http_code}' \
        -X PATCH "$BASE_URL/api/celdas/C08/deshabilitar" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{}' \
        > "$TMP_DIR/celda.code"
) &
PID_CELDA=$!
wait "$PID_ENTRADA" "$PID_CELDA"
ce06_entry="$(cat "$TMP_DIR/entrada.code")"
ce06_disable="$(cat "$TMP_DIR/celda.code")"
ce06_state="$(db_scalar "SELECT estado FROM celda WHERE codigo='C08';")"
ce06_success=0
[ "$ce06_entry" = "201" ] && ce06_success=$((ce06_success + 1))
[ "$ce06_disable" = "200" ] && ce06_success=$((ce06_success + 1))
ce06_consistent=false
if [ "$ce06_success" -eq 1 ] && { [ "$ce06_state" = "OCUPADA" ] || [ "$ce06_state" = "FUERA_DE_SERVICIO" ]; }; then
    ce06_consistent=true
fi
if [ "$ce06_state" = "OCUPADA" ]; then
    request "POST" "/api/salidas" "$OPERADOR1_TOKEN" '{"placa":"DEF456"}'
elif [ "$ce06_state" = "FUERA_DE_SERVICIO" ]; then
    request "PATCH" "/api/celdas/C08/habilitar" "$ADMIN_TOKEN" '{}'
fi
rm -rf "$TMP_DIR"
if [ "$ce06_consistent" = "true" ]; then
    mostrar_resultado "CE-06" "PASS" "Entrada y deshabilitación concurrentes: solo una prospera y el estado final es coherente."
else
    mostrar_resultado "CE-06" "FAIL" "La concurrencia dejó un resultado inesperado (entrada=$ce06_entry, deshabilitar=$ce06_disable, estado=$ce06_state)."
fi

# RG-01 - Regresión entrada/salida e integridad de estancia
request "POST" "/api/entradas" "$OPERADOR1_TOKEN" '{"placa":"ABC123","codigo_celda":"C01"}'
rg01_entry="$HTTP_STATUS"
request "POST" "/api/entradas" "$OPERADOR1_TOKEN" '{"placa":"ABC123","codigo_celda":"C02"}'
rg01_repeat_entry="$HTTP_STATUS"
request "POST" "/api/salidas" "$OPERADOR1_TOKEN" '{"placa":"ABC123"}'
rg01_exit="$HTTP_STATUS"
request "POST" "/api/salidas" "$OPERADOR1_TOKEN" '{"placa":"ABC123"}'
rg01_repeat_exit="$HTTP_STATUS"
rg01_sql_output="$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$PROJECT_ROOT/sql/pruebas_integridad_estancia.sql" 2>&1)"
rg01_pass_count="$(printf '%s\n' "$rg01_sql_output" | grep -c 'PASS:')"
if [ "$rg01_entry" = "201" ] && [ "$rg01_repeat_entry" = "400" ] \
    && [ "$rg01_exit" = "200" ] && [ "$rg01_repeat_exit" = "400" ] \
    && [ "$rg01_pass_count" = "6" ]; then
    mostrar_resultado "RG-01" "PASS" "Entrada/salida mantienen comportamiento EA1 y P-14 a P-19 aprueban integridad."
else
    mostrar_resultado "RG-01" "FAIL" "Falló alguna regresión de entrada/salida o integridad de estancia."
fi

# RG-02 - Consultas de EA1 con y sin sesión
request "GET" "/api/estancias/activas" "$OPERADOR1_TOKEN"
rg02_active_auth="$HTTP_STATUS"
request "GET" "/api/parqueadero/estado" "$OPERADOR1_TOKEN"
rg02_state_auth="$HTTP_STATUS"
request "GET" "/api/celdas/disponibles?tipo_vehiculo=MOTO" "$OPERADOR1_TOKEN"
rg02_cells_auth="$HTTP_STATUS"
request "GET" "/api/estancias/activas"
rg02_active_no="$HTTP_STATUS"
request "GET" "/api/parqueadero/estado"
rg02_state_no="$HTTP_STATUS"
request "GET" "/api/celdas/disponibles?tipo_vehiculo=MOTO"
rg02_cells_no="$HTTP_STATUS"
if [ "$rg02_active_auth" = "200" ] && [ "$rg02_state_auth" = "200" ] \
    && [ "$rg02_cells_auth" = "200" ] && [ "$rg02_active_no" = "401" ] \
    && [ "$rg02_state_no" = "401" ] && [ "$rg02_cells_no" = "401" ]; then
    mostrar_resultado "RG-02" "PASS" "Consultas EA1 funcionan con sesión y rechazan acceso sin sesión."
else
    mostrar_resultado "RG-02" "FAIL" "Alguna consulta heredada no respetó sesión/autenticación."
fi

cleanup_final

echo
echo "=========================================="
echo "RESUMEN"
echo "PASS: $PASS"
echo "FAIL: $FAIL"
echo "TOTAL: $((PASS + FAIL))"
echo "=========================================="

if [ "$FAIL" -eq 0 ]; then
    exit 0
else
    exit 1
fi
