Chart.defaults.color = '#cfe3ff';
Chart.defaults.borderColor = 'rgba(255,255,255,.08)';
Chart.defaults.font.family = 'Montserrat, Roboto, system-ui';

function round2(n){ return Math.round(n*100)/100; }

const form = document.getElementById('formCalculo');
const genDiaEl = document.getElementById('genDia');
const genMesEl = document.getElementById('genMes');
const coberturaEl = document.getElementById('cobertura');
const ahorroEl = document.getElementById('ahorro');
const kwhMesCard = document.getElementById('kwhMes');
const ahorroMesCard = document.getElementById('ahorroMes');

let serieGeneracion = Array(12).fill(0);
let serieAhorro = Array(12).fill(0);

form?.addEventListener('submit', (e) => {
  e.preventDefault();

  const consumoDiario = parseFloat(document.getElementById('consumoDiario').value);
  const irradiacion   = parseFloat(document.getElementById('irradiacion').value);
  const potenciaPanel = parseFloat(document.getElementById('potenciaPanel').value);
  const numPaneles    = parseFloat(document.getElementById('numPaneles').value);
  const eficiencia    = parseFloat(document.getElementById('eficiencia').value) / 100;
  const precioKwh     = parseFloat(document.getElementById('precioKwh').value);

  const genDia = (potenciaPanel * numPaneles / 1000) * irradiacion * eficiencia;
  const genMes = genDia * 30;
  const cobertura = Math.min(100, (genDia / consumoDiario) * 100);
  const ahorroMes = genMes * precioKwh;

  genDiaEl.textContent = round2(genDia);
  genMesEl.textContent = round2(genMes);
  coberturaEl.textContent = round2(cobertura);
  ahorroEl.textContent = `$${Math.round(ahorroMes).toLocaleString('es-CL')}`;

  kwhMesCard.textContent = `${round2(genMes)} kWh`;
  ahorroMesCard.textContent = `$${Math.round(ahorroMes).toLocaleString('es-CL')}`;

  serieGeneracion = Array(12).fill(round2(genMes));
  serieAhorro = Array(12).fill(Math.round(ahorroMes));

  renderCharts();
});

let chartGen, chartAhorro;
function renderCharts(){
  const labels = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];

  if(chartGen) chartGen.destroy();
  chartGen = new Chart(document.getElementById('graficoGeneracion'), {
    type: 'line',
    data: { labels, datasets: [{ label: 'Generación mensual (kWh)', data: serieGeneracion, borderWidth: 2 }] }
  });

  if(chartAhorro) chartAhorro.destroy();
  chartAhorro = new Chart(document.getElementById('graficoAhorro'), {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Ahorro mensual ($)', data: serieAhorro }] }
  });
}
