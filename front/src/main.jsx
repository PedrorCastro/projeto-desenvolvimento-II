import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, CloudRain, Droplets, Gauge, Leaf, Lightbulb, RefreshCw, Thermometer, Wifi } from 'lucide-react';
import './styles.css';

const API_URL = import.meta.env.VITE_API_URL || 'https://projeto-desenvolvimento-ii.onrender.com';
const stationId = 'esp32-campus-01';

function formatTime(value) { return value ? new Date(value).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '--:--'; }
function formatDate(value) { return value ? new Date(value).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }) : ''; }

function Metric({ icon: Icon, label, value, unit, tone }) {
  return <article className={`metric metric-${tone}`}><div className="metric-icon"><Icon size={19} /></div><div><span>{label}</span><strong>{value ?? '--'}<small>{unit}</small></strong></div></article>;
}

function Chart({ data, field, color, label, unit }) {
  const points = useMemo(() => data.slice().reverse().map((item, i, all) => {
    const values = all.map(entry => Number(entry[field]) || 0); const min = Math.min(...values); const max = Math.max(...values); const range = max - min || 1;
    return `${(i / Math.max(all.length - 1, 1)) * 100},${88 - ((Number(item[field]) - min) / range) * 64}`;
  }).join(' '), [data, field]);
  return <section className="chart-card"><div className="chart-heading"><div><span className="eyebrow">Tendência</span><h3>{label}</h3></div><span className="chart-unit">{unit}</span></div>{data.length ? <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="chart"><polyline points={points} fill="none" stroke={color} strokeWidth="2.8" vectorEffect="non-scaling-stroke" /></svg> : <div className="chart-empty">Aguardando medições suficientes</div>}<div className="chart-axis"><span>{formatDate(data.at(-1)?.measured_at)}</span><span>{formatDate(data[0]?.measured_at)}</span></div></section>;
}

function App() {
  const [latest, setLatest] = useState(null); const [history, setHistory] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [updated, setUpdated] = useState(null);
  async function loadData() { setLoading(true); setError(''); try { const [current, list] = await Promise.all([fetch(`${API_URL}/api/v1/stations/${stationId}/latest`), fetch(`${API_URL}/api/v1/measurements?station_id=${stationId}&limit=50`)]); if (!current.ok || !list.ok) throw new Error('A API não respondeu corretamente.'); setLatest(await current.json()); setHistory((await list.json()).measurements || []); setUpdated(new Date()); } catch (err) { setError(err.message); } finally { setLoading(false); } }
  useEffect(() => { loadData(); const timer = setInterval(loadData, 30000); return () => clearInterval(timer); }, []);
  return <main><header className="topbar"><div className="brand"><div className="brand-mark"><Activity size={21} /></div><div><strong>Meteo<span>Cidade</span></strong><small>monitoramento ambiental urbano</small></div></div><div className="top-actions"><div className="station"><span className="status-dot" /> <span>Campus Centro</span><small>ESP32 • {stationId}</small></div><button className="refresh" onClick={loadData} aria-label="Atualizar dados"><RefreshCw size={17} className={loading ? 'spin' : ''} /></button></div></header>
    <section className="hero"><div><p className="eyebrow">Painel em tempo real</p><h1>O pulso do clima<br /><em>no campus.</em></h1><p className="intro">Leituras ambientais captadas pelo ESP32 e atualizadas automaticamente.</p></div><div className="hero-status"><Wifi size={17} /><div><strong>Estação online</strong><span>Atualização automática a cada 30 segundos</span></div></div></section>
    {error && <div className="alert"><span>Não foi possível atualizar os dados.</span><button onClick={loadData}>Tentar novamente</button></div>}
    <section className="metrics"><Metric icon={Thermometer} label="Temperatura" value={latest?.temperature_c?.toFixed(1)} unit="°C" tone="orange" /><Metric icon={Droplets} label="Umidade relativa" value={latest?.humidity_pct?.toFixed(1)} unit="%" tone="blue" /><Metric icon={Gauge} label="Pressão atmosférica" value={latest?.pressure_hpa?.toFixed(1)} unit="hPa" tone="purple" /><Metric icon={Leaf} label="Qualidade do ar" value={latest?.air_quality_raw?.toFixed(0)} unit="raw" tone="green" /><Metric icon={Lightbulb} label="Luminosidade" value={latest?.luminosity_raw?.toFixed(0)} unit="raw" tone="yellow" /><Metric icon={CloudRain} label="Chuva acumulada" value={latest?.rainfall_mm?.toFixed(1)} unit="mm" tone="cyan" /></section>
    <section className="section-title"><div><p className="eyebrow">Janela de observação</p><h2>Últimas medições</h2></div><span className="last-update">{updated ? `Sincronizado às ${formatTime(updated)}` : 'Sincronizando...'}</span></section>
    <section className="charts"><Chart data={history} field="temperature_c" color="#ff9f43" label="Temperatura" unit="°C" /><Chart data={history} field="humidity_pct" color="#4cc9f0" label="Umidade relativa" unit="%" /></section>
    <section className="feed"><div className="feed-heading"><div><p className="eyebrow">Dados recebidos</p><h2>Leituras recentes</h2></div><span>{history.length} registros</span></div><div className="table-wrap"><table><thead><tr><th>Horário</th><th>Temperatura</th><th>Umidade</th><th>Pressão</th><th>Estado</th></tr></thead><tbody>{history.slice(0, 6).map(item => <tr key={item.id}><td>{formatTime(item.measured_at)}</td><td>{item.temperature_c?.toFixed(1)} °C</td><td>{item.humidity_pct?.toFixed(1)}%</td><td>{item.pressure_hpa?.toFixed(1)} hPa</td><td><span className="normal"><i /> Normal</span></td></tr>)}</tbody></table></div></section>
    <footer><span>METEOCIDADE / PD-II</span><span>Fonte: {stationId} • {latest ? `última leitura ${formatTime(latest.measured_at)}` : 'sem leitura'}</span></footer>
  </main>;
}
createRoot(document.getElementById('root')).render(<App />);
