<?php 
include('db.php'); 
date_default_timezone_set('America/Argentina/Buenos_Aires');

$mensaje_exito = "";

// --- EXCEL (Agregado el año en el reporte) ---
if(isset($_GET['exportar'])){
    header("Content-Type: application/vnd.ms-excel");
    header("Content-Disposition: attachment; filename=reporte_odm.xls");
    $res = mysqli_query($conn, "SELECT * FROM odms");
    echo "ID\tFecha Creado\tTitulo\tResponsable\tPrioridad\tEstado\n";
    while($r = mysqli_fetch_assoc($res)) {
        $f_excel = date('d/m/Y', strtotime($r['fecha_creacion']));
        echo "{$r['id']}\t{$f_excel}\t{$r['titulo']}\t{$r['responsable']}\t{$r['prioridad']}\t{$r['estado']}\n";
    }
    exit;
}

// --- GUARDAR / EDITAR (Mismo código original) ---
if(isset($_POST['guardar'])){
    $titulo = mysqli_real_escape_string($conn, $_POST['titulo']);
    $resp = mysqli_real_escape_string($conn, $_POST['responsable']);
    $prio = mysqli_real_escape_string($conn, $_POST['prioridad']);
    $desc = mysqli_real_escape_string($conn, $_POST['descripcion']);
    $coment = mysqli_real_escape_string($conn, $_POST['comentarios'] ?? '');
    $fecha_est = $_POST['fecha_estimada'];
    $estado = $_POST['estado'] ?? 'Abierta';

    if(!empty($titulo) && !empty($resp) && !empty($prio)){
        if(!empty($_POST['id_edit'])){
            $id = $_POST['id_edit'];
            mysqli_query($conn, "UPDATE odms SET titulo='$titulo', responsable='$resp', prioridad='$prio', descripcion='$desc', comentarios='$coment', fecha_estimada='$fecha_est', estado='$estado' WHERE id=$id");
            header("Location: index.php?msg=editado&id=$id");
        } else {
            mysqli_query($conn, "INSERT INTO odms (titulo, responsable, prioridad, descripcion, fecha_estimada) VALUES ('$titulo', '$resp', '$prio', '$desc', '$fecha_est')");
            $nuevo_id = mysqli_insert_id($conn);
            header("Location: index.php?msg=creado&id=$nuevo_id");
        }
        exit;
    }
}

if(isset($_GET['msg'])){
    $id_msg = $_GET['id'];
    if($_GET['msg'] == 'creado') $mensaje_exito = "¡La ODM #$id_msg ha sido creada con éxito!";
    if($_GET['msg'] == 'editado') $mensaje_exito = "La ODM #$id_msg se actualizó correctamente.";
}

if(isset($_POST['borrar'])){
    $id_b = $_POST['id_borrar'];
    mysqli_query($conn, "DELETE FROM odms WHERE id=$id_b");
    $check = mysqli_fetch_assoc(mysqli_query($conn, "SELECT COUNT(*) as t FROM odms"));
    if($check['t'] == 0) mysqli_query($conn, "ALTER TABLE odms AUTO_INCREMENT = 1");
    header("Location: index.php");
}

$where_base = "1=1";
if(!empty($_GET['f_resp'])) $where_base .= " AND responsable='{$_GET['f_resp']}'";
if(!empty($_GET['f_prio'])) $where_base .= " AND prioridad='{$_GET['f_prio']}'";
$counts = mysqli_fetch_assoc(mysqli_query($conn, "SELECT SUM(estado='Abierta') as a, SUM(estado='En curso') as e, SUM(estado='Cerrada') as c FROM odms"));
?>

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Oportunidades de mejora Gurum</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #0d2a54; color: white; }
        .card { color: #333; }
        .badge-alta { background-color: #dc3545; color: white; }
        .badge-media { background-color: #ffc107; color: black; }
        .badge-baja { background-color: #e9ecef; color: #333; border: 1px solid #ccc; }
        .badge-abierta { background-color: #198754; color: white; }
        .badge-curso { background-color: #fd7e14; color: white; }
        .badge-cerrada { background-color: #6c757d; color: white; }
        h4 { color: #ffc107; border-bottom: 1px solid #ffffff33; padding-bottom: 10px; margin-top: 10px; }
        .btn-footer { background-color: #4b6584; color: white; border: none; font-weight: bold; }
        .btn-footer:hover { background-color: #778ca3; color: white; }

        /* --- NUEVO: Scroll para las tablas --- */
        .table-responsive { 
            max-height: 500px; 
            overflow-y: auto; 
            border-radius: 5px;
        }
        /* Esto deja el encabezado quieto al scrollear */
        .table thead th { 
            position: sticky; 
            top: 0; 
            z-index: 10; 
            background-color: #212529 !important; 
        }
    </style>
</head>
<body class="pb-5">
    <div class="container py-4">
        <div class="text-center mb-4">
            <img src="gurumcafe.jpg" style="max-width: 120px; border-radius: 10px; border: 2px solid white;">
            <h2 class="mt-2 text-white">Oportunidades de mejora Gurum</h2>
        </div>

        <?php if($mensaje_exito): ?>
            <div class="alert alert-success alert-dismissible fade show shadow-sm fw-bold text-center" role="alert">
                <?php echo $mensaje_exito; ?>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        <?php endif; ?>

        <div class="d-grid gap-2 mb-4">
            <button class="btn btn-success btn-lg fw-bold shadow" type="button" data-bs-toggle="collapse" data-bs-target="#collapseForm">
                + CARGAR NUEVA ODM
            </button>
        </div>

        <?php 
        $edit = null; $bloqueado = ""; $show_form = "";
        if(isset($_GET['edit'])){
            $id_edit = $_GET['edit'];
            $edit = mysqli_fetch_assoc(mysqli_query($conn, "SELECT * FROM odms WHERE id=$id_edit"));
            if($edit['estado'] == 'Cerrada') $bloqueado = "disabled"; 
            $show_form = "show";
        }
        ?>

        <div class="collapse <?php echo $show_form; ?> mb-4" id="collapseForm">
            <div class="card shadow">
                <div class="card-header bg-primary text-white fw-bold">
                    <?php echo $edit ? ($bloqueado ? 'VISUALIZANDO ODM #' : 'EDITANDO ODM #').$edit['id'] : 'REGISTRO DE NUEVA ODM'; ?>
                </div>
                <div class="card-body">
                    <form method="POST" class="row g-3">
                        <input type="hidden" name="id_edit" value="<?php echo $edit['id'] ?? ''; ?>">
                        <div class="col-md-5"><label class="form-label small fw-bold">Título de la ODM *</label><input type="text" name="titulo" class="form-control" value="<?php echo $edit['titulo'] ?? ''; ?>" required <?php echo $bloqueado; ?>></div>
                        <div class="col-md-4"><label class="form-label small fw-bold">Responsable *</label>
                            <select name="responsable" class="form-select" required <?php echo $bloqueado; ?>>
                                <option value="">Seleccionar...</option>
                                <?php $staff = ["Ezequiel Caceres", "Federico Kong", "Aldana Molina", "Micaela Cardozo"];
                                foreach($staff as $s) echo "<option value='$s' ".((@$edit['responsable']==$s)?'selected':'').">$s</option>"; ?>
                            </select>
                        </div>
                        <div class="col-md-3"><label class="form-label small fw-bold">Prioridad *</label>
                            <select name="prioridad" class="form-select" required <?php echo $bloqueado; ?>>
                                <option value="">Seleccionar...</option>
                                <option value="Alta" <?php echo (@$edit['prioridad']=='Alta')?'selected':''; ?>>Alta</option>
                                <option value="Media" <?php echo (@$edit['prioridad']=='Media')?'selected':''; ?>>Media</option>
                                <option value="Baja" <?php echo (@$edit['prioridad']=='Baja')?'selected':''; ?>>Baja</option>
                            </select>
                        </div>
                        <div class="col-md-3"><label class="form-label small fw-bold">Estado Actual</label>
                            <select name="estado" class="form-select" <?php echo $bloqueado; ?>>
                                <option value="Abierta" <?php echo (@$edit['estado']=='Abierta')?'selected':''; ?>>Abierta</option>
                                <option value="En curso" <?php echo (@$edit['estado']=='En curso')?'selected':''; ?>>En curso</option>
                                <option value="Cerrada" <?php echo (@$edit['estado']=='Cerrada')?'selected':''; ?>>Cerrada</option>
                            </select>
                        </div>
                        <div class="col-md-3"><label class="form-label small fw-bold">Fecha Estimada</label><input type="date" name="fecha_estimada" class="form-control" value="<?php echo $edit['fecha_estimada'] ?? ''; ?>" <?php echo $bloqueado; ?>></div>
                        <div class="col-md-6"><label class="form-label small fw-bold">Descripción</label><textarea name="descripcion" class="form-control" rows="1" <?php echo $bloqueado; ?>><?php echo $edit['descripcion'] ?? ''; ?></textarea></div>
                        <?php if($edit): ?><div class="col-12"><label class="form-label small fw-bold text-primary">Comentarios</label><textarea name="comentarios" class="form-control" rows="2" <?php echo $bloqueado; ?>><?php echo $edit['comentarios'] ?? ''; ?></textarea></div><?php endif; ?>
                        
                        <div class="col-12 text-end">
                            <a href="index.php" class="btn btn-secondary btn-sm">Cerrar</a>
                            <?php if(!$bloqueado): ?><button type="submit" name="guardar" class="btn btn-success btn-sm px-4">Guardar Cambios</button><?php endif; ?>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <div class="d-flex justify-content-between mb-4 bg-white p-2 rounded shadow-sm text-dark">
            <form class="row g-2 align-items-center">
                <div class="col-auto"><select name="f_resp" class="form-select form-select-sm"><option value="">Responsable...</option><?php foreach($staff as $s) echo "<option value='$s'>$s</option>"; ?></select></div>
                <div class="col-auto"><select name="f_prio" class="form-select form-select-sm"><option value="">Prioridad...</option><option>Alta</option><option>Media</option><option>Baja</option></select></div>
                <div class="col-auto"><button type="submit" class="btn btn-sm btn-dark">Filtrar</button><a href="index.php" class="btn btn-sm btn-outline-danger ms-1">X</a></div>
            </form>
            <a href="index.php?exportar=1" class="btn btn-sm btn-success">Excel</a>
        </div>

        <h4>ODMs Activas</h4>
        <div class="table-responsive mb-4 shadow-sm">
            <table class="table table-light table-hover align-middle">
                <thead class="table-dark text-center">
                    <tr><th>ID</th><th>Fecha de creación</th><th>Título ODM</th><th>Responsable</th><th>Prioridad</th><th>Estado</th><th>Acción</th></tr>
                </thead>
                <tbody class="text-center">
                    <?php 
                    $res_activas = mysqli_query($conn, "SELECT * FROM odms WHERE ($where_base) AND estado != 'Cerrada' ORDER BY id DESC");
                    while($row = mysqli_fetch_assoc($res_activas)){
                        $p_class = "badge-" . strtolower($row['prioridad']);
                        $e_class = "badge-" . ($row['estado']=='En curso' ? 'curso' : strtolower($row['estado']));
                        $fecha_c = date('d/m/Y', strtotime($row['fecha_creacion']));
                        echo "<tr>
                            <td class='fw-bold'>#{$row['id']}</td>
                            <td>$fecha_c</td>
                            <td class='text-start'><strong>{$row['titulo']}</strong><br><small class='text-muted'>{$row['descripcion']}</small></td>
                            <td>{$row['responsable']}</td>
                            <td><span class='badge $p_class px-3'>{$row['prioridad']}</span></td>
                            <td><span class='badge $e_class px-3'>{$row['estado']}</span></td>
                            <td><a href='index.php?edit={$row['id']}' class='btn btn-sm btn-warning fw-bold'>EDITAR</a></td>
                        </tr>";
                    } ?>
                </tbody>
            </table>
        </div>

        <div class="mt-5">
            <button class="btn btn-outline-secondary text-white w-100 mb-3 fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#collapseHistorial">
                VER HISTORIAL DE CERRADAS
            </button>
            <div class="collapse" id="collapseHistorial">
                <div class="table-responsive shadow-sm">
                    <table class="table table-secondary table-hover align-middle opacity-75">
                        <thead class="table-dark text-center">
                            <tr><th>ID</th><th>Fecha de creación</th><th>Título ODM</th><th>Responsable</th><th>Prioridad</th><th>Estado</th><th>Info</th></tr>
                        </thead>
                        <tbody class="text-center text-dark">
                            <?php 
                            $res_cerradas = mysqli_query($conn, "SELECT * FROM odms WHERE ($where_base) AND estado = 'Cerrada' ORDER BY id DESC");
                            while($row = mysqli_fetch_assoc($res_cerradas)){
                                $p_class = "badge-" . strtolower($row['prioridad']);
                                $fecha_c = date('d/m/Y', strtotime($row['fecha_creacion']));
                                echo "<tr>
                                    <td>#{$row['id']}</td>
                                    <td>$fecha_c</td>
                                    <td class='text-start'><strong>{$row['titulo']}</strong><br><small>{$row['descripcion']}</small></td>
                                    <td>{$row['responsable']}</td>
                                    <td><span class='badge $p_class px-2'>{$row['prioridad']}</span></td>
                                    <td><span class='badge badge-cerrada px-3'>Cerrada</span></td>
                                    <td><a href='index.php?edit={$row['id']}' class='btn btn-sm btn-primary'>VER</a></td>
                                </tr>";
                            } ?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="mt-5 pt-4 border-top">
            <button class="btn btn-footer w-100 mb-2" type="button" data-bs-toggle="collapse" data-bs-target="#collapseStats">📊 VER ESTADÍSTICAS</button>
            <div class="collapse mb-4" id="collapseStats">
                <div class="card card-body bg-white shadow-sm" style="max-width: 300px; margin: auto;">
                    <canvas id="graficoEstados"></canvas>
                </div>
            </div>

            <button class="btn btn-footer w-100" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOtros">⚙️ OTRAS ACCIONES</button>
            <div class="collapse mt-2" id="collapseOtros">
                <div class="card card-body bg-light border-danger shadow-sm text-center text-dark">
                    <h6 class="fw-bold text-danger mb-3">Borrar ODM por ID:</h6>
                    <form method="POST" onsubmit="return confirm('¿Borrar permanentemente?');" class="input-group" style="max-width: 300px; margin: auto;">
                        <input type="number" name="id_borrar" class="form-control border-danger" required placeholder="ID">
                        <button type="submit" name="borrar" class="btn btn-danger">BORRAR</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const ctx = document.getElementById('graficoEstados');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Abiertas', 'En curso', 'Cerradas'],
                datasets: [{
                    data: [<?php echo (int)$counts['a']; ?>, <?php echo (int)$counts['e']; ?>, <?php echo (int)$counts['c']; ?>],
                    backgroundColor: ['#198754', '#fd7e14', '#6c757d']
                }]
            },
            options: { plugins: { legend: { position: 'bottom' } } }
        });
    </script>
</body>
</html>