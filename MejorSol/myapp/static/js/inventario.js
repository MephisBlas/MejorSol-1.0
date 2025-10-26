(() => {
  const q  = (sel, ctx=document) => ctx.querySelector(sel);
  const qa = (sel, ctx=document) => Array.from(ctx.querySelectorAll(sel));

  const buscar = q('#buscar');
  const filtroCat = q('#filtroCategoria');
  const filtroEstado = q('#filtroEstado');
  const tbody = q('#tbodyInventario');

  const modal = q('#modalForm');
  const openBtn = q('#btnNuevo');
  const closeBtn = q('#closeModal');
  const cancelBtn = q('#cancelar');
  const formProducto = q('#formProducto');
  const modalTitle = q('#modalTitle');

  const sku = q('#sku'), nombre = q('#nombre'), categoria = q('#categoria');
  const stock = q('#stock'), minimo = q('#minimo'), precio = q('#precio');

  const exportBtn = q('#btnExport');

  // ----- Filtros -----
  function aplicaFiltros(){
    const term = (buscar.value || '').toLowerCase();
    const cat = filtroCat.value;
    const est = filtroEstado.value; // '' | 'ok' | 'bajo'

    qa('tr', tbody).forEach(tr => {
      const cells = tr.children;
      if(!cells.length) return; // fila vacía

      const tSku = (tr.dataset.sku || '').toLowerCase();
      const tNombre = (cells[1].textContent || '').toLowerCase();
      const tCat = tr.dataset.categoria || cells[2].textContent;
      const tStock = parseFloat(cells[3].textContent) || 0;
      const tMin = parseFloat(cells[4].textContent) || 0;

      const estado = tStock <= tMin ? 'bajo' : 'ok';

      const matchTxt = tSku.includes(term) || tNombre.includes(term);
      const matchCat = !cat || tCat === cat;
      const matchEst = !est || estado === est;

      tr.style.display = (matchTxt && matchCat && matchEst) ? '' : 'none';
    });
  }
  buscar?.addEventListener('input', aplicaFiltros);
  filtroCat?.addEventListener('change', aplicaFiltros);
  filtroEstado?.addEventListener('change', aplicaFiltros);

  // ----- Modal -----
  function openModal(editing=false, tr=null){
    modal.classList.add('show');
    modal.setAttribute('aria-hidden','false');
    modalTitle.textContent = editing ? 'Editar producto' : 'Nuevo producto';

    formProducto.dataset.mode = editing ? 'edit' : 'new';
    formProducto.dataset.row = editing ? tr?.rowIndex : '';

    if(editing && tr){
      sku.value = tr.children[0].textContent.trim();
      nombre.value = tr.children[1].textContent.trim();
      categoria.value = tr.children[2].textContent.trim();
      stock.value = parseFloat(tr.children[3].textContent) || 0;
      minimo.value = parseFloat(tr.children[4].textContent) || 0;
      precio.value = parseInt(tr.children[6].textContent.replace(/[^\d]/g,'')) || 0;
      sku.readOnly = true; // no alterar SKU al editar
    } else {
      formProducto.reset();
      stock.value = 0; minimo.value = 0; precio.value = 0;
      sku.readOnly = false;
    }
  }
  function closeModalFn(){
    modal.classList.remove('show');
    modal.setAttribute('aria-hidden','true');
  }

  openBtn?.addEventListener('click', () => openModal(false, null));
  closeBtn?.addEventListener('click', closeModalFn);
  cancelBtn?.addEventListener('click', closeModalFn);
  modal?.addEventListener('click', (e)=>{ if(e.target === modal) closeModalFn(); });

  // ----- CRUD (frontend demo) -----
  formProducto?.addEventListener('submit', (e)=>{
    e.preventDefault();

    const data = {
      sku: sku.value.trim(),
      nombre: nombre.value.trim(),
      categoria: categoria.value,
      stock: Math.max(0, parseFloat(stock.value)||0),
      minimo: Math.max(0, parseFloat(minimo.value)||0),
      precio: Math.max(0, parseFloat(precio.value)||0),
    };

    if(!data.sku || !data.nombre) return;

    if(formProducto.dataset.mode === 'edit'){
      // actualizar fila existente
      const tr = [...tbody.rows].find(r => r.children[0].textContent.trim() === data.sku);
      if(tr){
        tr.dataset.sku = data.sku;
        tr.dataset.categoria = data.categoria;
        tr.children[1].textContent = data.nombre;
        tr.children[2].textContent = data.categoria;
        tr.children[3].textContent = data.stock;
        tr.children[4].textContent = data.minimo;
        tr.children[6].textContent = data.precio.toLocaleString('es-CL');

        const estadoCell = tr.children[5];
        estadoCell.innerHTML = (data.stock <= data.minimo)
          ? '<span class="badge danger">Bajo</span>'
          : '<span class="badge ok">OK</span>';
      }
    } else {
      // crear nueva fila
      const tr = document.createElement('tr');
      tr.dataset.sku = data.sku;
      tr.dataset.categoria = data.categoria;
      tr.innerHTML = `
        <td>${data.sku}</td>
        <td>${data.nombre}</td>
        <td>${data.categoria}</td>
        <td class="num">${data.stock}</td>
        <td class="num">${data.minimo}</td>
        <td>${data.stock <= data.minimo ? '<span class="badge danger">Bajo</span>' : '<span class="badge ok">OK</span>'}</td>
        <td class="num">${data.precio.toLocaleString('es-CL')}</td>
        <td class="actions">
          <button class="btn-icon in" title="Entrada"><i class="fas fa-arrow-down"></i></button>
          <button class="btn-icon out" title="Salida"><i class="fas fa-arrow-up"></i></button>
          <button class="btn-icon edit" title="Editar"><i class="fas fa-pen"></i></button>
          <button class="btn-icon delete" title="Eliminar"><i class="fas fa-trash"></i></button>
        </td>`;
      tbody.appendChild(tr);
      bindRowActions(tr);
    }

    closeModalFn();
    aplicaFiltros();
  });

  // acciones por fila: entrada/salida/editar/eliminar
  function bindRowActions(tr){
    tr.querySelector('.in')?.addEventListener('click', () => moverStock(tr, +1));
    tr.querySelector('.out')?.addEventListener('click', () => moverStock(tr, -1));
    tr.querySelector('.edit')?.addEventListener('click', () => openModal(true, tr));
    tr.querySelector('.delete')?.addEventListener('click', () => {
      if(confirm('¿Eliminar producto?')) tr.remove();
    });
  }
  qa('#tbodyInventario tr').forEach(bindRowActions);

  function moverStock(tr, dir){
    const qty = parseFloat(prompt(dir>0 ? 'Cantidad de entrada:' : 'Cantidad de salida:')) || 0;
    if(qty <= 0) return;
    const stockCell = tr.children[3];
    let st = parseFloat(stockCell.textContent) || 0;
    st = Math.max(0, st + dir*qty);
    stockCell.textContent = st;

    const minimo = parseFloat(tr.children[4].textContent) || 0;
    tr.children[5].innerHTML = (st <= minimo) ? '<span class="badge danger">Bajo</span>' : '<span class="badge ok">OK</span>';
  }

  // ----- Exportar CSV (filas visibles) -----
  exportBtn?.addEventListener('click', ()=>{
    const rows = qa('#tablaInventario tr');
    let csv = [];
    rows.forEach((r, i) => {
      if(i===0){ // encabezados
        csv.push(qa('th', r).map(th => th.innerText).join(','));
        return;
      }
      if(r.style.display === 'none') return;
      const cols = qa('td', r);
      if(!cols.length) return;
      csv.push([
        cols[0].innerText, cols[1].innerText, cols[2].innerText,
        cols[3].innerText, cols[4].innerText,
        cols[5].innerText.replace(/,/g,''), // estado
        cols[6].innerText.replace(/\./g,'').replace(/,/g,''), // precio limpio
      ].join(','));
    });

    const blob = new Blob([csv.join('\n')], {type:'text/csv;charset=utf-8;'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'inventario.csv';
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  });

  // Nota: para producción, reemplaza prompts & client-side por llamadas fetch() a tus endpoints Django.
})();
