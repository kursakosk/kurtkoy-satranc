import streamlit as st
import pandas as pd
import random
import os
import copy
from datetime import datetime
from fpdf import FPDF

# --- Sayfa Ayarları ---
st.set_page_config(
    page_title="Kurtköy Satranç SK Turnuva Sistemi",
    page_icon="♟️",
    layout="wide"
)

# --- Session State (Hafıza) ---
if 'players' not in st.session_state:
    st.session_state.players = [] 
if 'deleted_players' not in st.session_state:
    st.session_state.deleted_players = []
if 'rounds_history' not in st.session_state:
    st.session_state.rounds_history = [] 
if 'current_pairings' not in st.session_state:
    st.session_state.current_pairings = []
if 'round_active' not in st.session_state:
    st.session_state.round_active = False
if 'tournament_finished' not in st.session_state:
    st.session_state.tournament_finished = False

# --- Yardımcı Fonksiyonlar ---

def tr_to_latin(text):
    """PDF için Türkçe karakterleri Latin karakterlere çevirir"""
    if not text: return ""
    text = str(text)
    mapping = {
        'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U',
        'ş': 's', 'Ş': 'S', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
    }
    for tr, latin in mapping.items():
        text = text.replace(tr, latin)
    return text

def create_pdf(type_doc, data, round_num, metadata):
    pdf = FPDF()
    pdf.add_page()
    
    # Logo
    if os.path.exists("logo.jpg"):
        pdf.image("logo.jpg", x=10, y=8, w=30)
    
    # Başlıklar
    pdf.set_y(15)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, tr_to_latin(metadata['name']), ln=True, align='C')
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, tr_to_latin(f"Tarih: {metadata['date']} | Yer: {metadata['location']}"), ln=True, align='C')
    
    if type_doc == "pairings":
        pdf.set_font("Arial", 'B', 14)
        pdf.ln(10)
        pdf.cell(0, 10, tr_to_latin(f"{round_num}. Tur Eslesmeleri"), ln=True, align='C')
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(15, 7, "Masa", 1)
        pdf.cell(70, 7, "Beyaz", 1)
        pdf.cell(20, 7, "Sonuc", 1)
        pdf.cell(70, 7, "Siyah", 1)
        pdf.ln()
        
        pdf.set_font("Arial", '', 10)
        for i, match in enumerate(data, 1):
            w = tr_to_latin(match['white']['name'])
            b_name = tr_to_latin(match['black']['name'])
            
            # Eğer rakip sanal bir 'BAY' ise
            if match.get('result') == 'BYE':
                 b_name = "BAY (Mac Yapmaz)"

            pdf.cell(15, 7, str(i), 1)
            pdf.cell(70, 7, w, 1)
            pdf.cell(20, 7, "_ - _", 1, align='C')
            pdf.cell(70, 7, b_name, 1)
            pdf.ln()

    elif type_doc == "standings":
        pdf.set_font("Arial", 'B', 14)
        pdf.ln(10)
        title = f"Final Siralama" if st.session_state.tournament_finished else f"{round_num}. Tur Sonrasi Siralama"
        pdf.cell(0, 10, tr_to_latin(title), ln=True, align='C')
        
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(10, 7, "Sira", 1)
        pdf.cell(60, 7, "Isim", 1)
        pdf.cell(15, 7, "ELO", 1)
        pdf.cell(15, 7, "Puan", 1)
        pdf.cell(15, 7, "Buc-1", 1)
        pdf.cell(15, 7, "Buc-T", 1)
        pdf.ln()
        
        pdf.set_font("Arial", '', 9)
        for i, p in enumerate(data, 1):
            pdf.cell(10, 7, str(i), 1)
            pdf.cell(60, 7, tr_to_latin(p['name']), 1)
            pdf.cell(15, 7, str(p['elo']), 1)
            pdf.cell(15, 7, str(p['score']), 1)
            pdf.cell(15, 7, str(p['buc1']), 1)
            pdf.cell(15, 7, str(p['buct']), 1)
            pdf.ln()

    # Alt Bilgi ve Bağış
    pdf.set_y(-40)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, tr_to_latin("Kurtkoy Satranc ve Akil Oyunlari Spor Kulubu - 2026"), ln=True, align='C')
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 9)
    pdf.multi_cell(0, 5, tr_to_latin("BAGIS BILGILENDIRME: Kulubumuzun gelisimi ve yeni materyaller icin yapacaginiz bagislar genclerimizin gelecegine isik tutacaktir. Desteginiz icin tesekkur ederiz."), align='C')
    
    return pdf.output(dest='S').encode('latin-1')

def calculate_metrics():
    """Buchholz hesaplar (Score -> Buc-1 -> Buc-T)"""
    for p in st.session_state.players:
        opp_scores = []
        for opp_name in p['opponents']:
            op = next((x for x in st.session_state.players if x['name'] == opp_name), None)
            if op:
                opp_scores.append(op['score'])
        
        p['buct'] = sum(opp_scores)
        if opp_scores:
            p['buc1'] = p['buct'] - min(opp_scores) 
        else:
            p['buc1'] = 0.0

def get_standings():
    calculate_metrics()
    # Sıralama: Puan -> Buc-1 -> Buc-T -> Elo
    sorted_players = sorted(
        st.session_state.players, 
        key=lambda x: (x['score'], x['buc1'], x['buct'], x['elo']), 
        reverse=True
    )
    return sorted_players

# --- Sidebar: Turnuva Bilgileri ---
with st.sidebar:
    st.image("logo.jpg", width=100) if os.path.exists("logo.jpg") else st.write("♟️")
    st.header("Turnuva Ayarları")
    
    t_name = st.text_input("Turnuva Adı", value="Kurtköy Satranç Turnuvası")
    t_date = st.date_input("Tarih", value=datetime.today())
    t_loc = st.text_input("Konum", value="Kulüp Merkezi")
    
    metadata = {'name': t_name, 'date': str(t_date), 'location': t_loc}
    
    st.divider()
    
    # Yeni Oyuncu Ekleme
    st.subheader("Oyuncu Ekle")
    with st.form("add_player"):
        p_name = st.text_input("Ad Soyad")
        p_elo = st.number_input("ELO Puanı", min_value=0, value=1000, step=10)
        add_btn = st.form_submit_button("Ekle")
        
        if add_btn:
            if p_name and not any(p['name'] == p_name for p in st.session_state.players):
                st.session_state.players.append({
                    'id': len(st.session_state.players)+1,
                    'name': p_name,
                    'elo': p_elo,
                    'score': 0.0,
                    'opponents': [],
                    'buc1': 0.0,
                    'buct': 0.0
                })
                st.success(f"{p_name} eklendi.")
            elif not p_name:
                st.warning("İsim giriniz.")
            else:
                st.warning("Bu isimde oyuncu zaten var.")

    st.info(f"Toplam Oyuncu: {len(st.session_state.players)}")
    
    # Çöp Kutusu (Geri Alma)
    with st.expander("🗑️ Silinen Oyuncular (Geri Al)"):
        if st.session_state.deleted_players:
            restore_name = st.selectbox("Geri al", [p['name'] for p in st.session_state.deleted_players])
            if st.button("Oyuncuyu Geri Getir"):
                p_to_restore = next(p for p in st.session_state.deleted_players if p['name'] == restore_name)
                st.session_state.players.append(p_to_restore)
                st.session_state.deleted_players.remove(p_to_restore)
                st.rerun()
        else:
            st.write("Çöp kutusu boş.")

    st.divider()
    if st.button("Turnuvayı Sıfırla (HER ŞEY SİLİNİR)", type="secondary"):
        st.session_state.clear()
        st.rerun()

# --- ANA EKRAN ---

st.title(t_name)
st.caption(f"📅 {t_date} | 📍 {t_loc}")

tab1, tab2, tab3 = st.tabs(["👥 Oyuncu Listesi & Düzenle", "⚔️ Turnuva Yönetimi", "📜 Geçmiş Turlar"])

# --- TAB 1: OYUNCU YÖNETİMİ ---
with tab1:
    if st.session_state.rounds_history:
        st.warning("Turnuva başladıktan sonra oyuncu silmek veya Elo değiştirmek teknik olarak önerilmez!")
    
    if st.session_state.players:
        df_players = pd.DataFrame(st.session_state.players)
        df_display = df_players[['name', 'elo', 'score']]
        
        # Sadece görüntüleme amaçlı tablo
        st.dataframe(
            df_display, 
            column_config={
                "name": "Ad Soyad", "elo": "ELO", "score": "Puan"
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown("---")
        st.subheader("Oyuncu Silme")
        col_del, col_info = st.columns(2)
        with col_del:
            to_delete = st.selectbox("Silinecek Oyuncu", ["Seçiniz"] + [p['name'] for p in st.session_state.players])
            if st.button("Seçili Oyuncuyu SİL"):
                if to_delete != "Seçiniz":
                    player_obj = next(p for p in st.session_state.players if p['name'] == to_delete)
                    st.session_state.deleted_players.append(player_obj)
                    st.session_state.players.remove(player_obj)
                    st.success(f"{to_delete} silindi.")
                    st.rerun()

# --- TAB 2: TURNUVA YÖNETİMİ ---
with tab2:
    if len(st.session_state.players) < 2:
        st.info("Turnuvaya başlamak için en az 2 oyuncu ekleyin.")
    elif st.session_state.tournament_finished:
        st.success("🏁 Turnuva Tamamlandı!")
        final_standings = get_standings()
        
        st.dataframe(
            pd.DataFrame(final_standings)[['name', 'elo', 'score', 'buc1', 'buct']],
            column_config={"name":"İsim", "elo":"Elo", "score":"Puan", "buc1":"Buc-1", "buct":"Buc-T"},
            hide_index=True
        )
        
        pdf_bytes = create_pdf("standings", final_standings, "FINAL", metadata)
        st.download_button("📥 Final Sonuçları PDF İndir", data=pdf_bytes, file_name="turnuva_final.pdf", mime="application/pdf")
        
    else:
        if not st.session_state.round_active:
            col_act1, col_act2 = st.columns([2, 1])
            with col_act1:
                btn_label = f"{len(st.session_state.rounds_history) + 1}. Tur Eşleşmelerini Yap"
                if st.button(btn_label, type="primary"):
                    players = st.session_state.players
                    # Kura algoritması
                    random.shuffle(players)
                    players.sort(key=lambda x: (x['score'], x['elo']), reverse=True)
                    
                    unpaired = players[:]
                    pairings = []
                    bye_player = None
                    
                    if len(unpaired) % 2 == 1:
                        bye_player = unpaired.pop() # En düşük puanlıyı bay geç
                    
                    while len(unpaired) > 0:
                        p1 = unpaired.pop(0)
                        found = False
                        for i, p2 in enumerate(unpaired):
                            if p2['name'] not in p1['opponents']:
                                pairings.append({'white': p1, 'black': p2, 'result': None})
                                unpaired.pop(i)
                                found = True
                                break
                        if not found and unpaired:
                             p2 = unpaired.pop(0)
                             pairings.append({'white': p1, 'black': p2, 'result': None})
                    
                    if bye_player:
                         pairings.append({'white': bye_player, 'black': {'name': 'BAY'}, 'result': 'BYE'})

                    st.session_state.current_pairings = pairings
                    st.session_state.round_active = True
                    st.rerun()
            
            with col_act2:
                if len(st.session_state.rounds_history) > 0:
                    if st.button("🏁 Turnuvayı Bitir"):
                        st.session_state.tournament_finished = True
                        st.rerun()

        else:
            round_num = len(st.session_state.rounds_history) + 1
            st.subheader(f"Masa Düzeni - {round_num}. Tur")
            
            pdf_pair = create_pdf("pairings", st.session_state.current_pairings, round_num, metadata)
            st.download_button("📥 Eşleşme Listesi (PDF)", data=pdf_pair, file_name=f"tur_{round_num}_eslesme.pdf", mime="application/pdf")
            
            with st.form("match_results"):
                results_submitted = []
                for i, match in enumerate(st.session_state.current_pairings, 1):
                    w = match['white']
                    b = match['black']
                    
                    if match.get('result') == 'BYE':
                        st.info(f"Masa {i}: {w['name']} BAY geçti (+1 Puan)")
                        results_submitted.append("BYE")
                        continue

                    c1, c2, c3 = st.columns([3, 2, 3])
                    with c1: st.write(f"⚪ {w['name']} ({w['elo']})")
                    with c2: 
                        res = st.selectbox(f"Masa {i} Sonuç", ["Seçiniz", "1-0", "0-1", "0.5-0.5"], key=f"res_{round_num}_{i}", label_visibility="collapsed")
                    with c3: st.write(f"⚫ {b['name']} ({b['elo']})")
                    st.markdown("---")
                    results_submitted.append(res)
                
                if st.form_submit_button("Sonuçları Kaydet ve Turu Bitir"):
                    if "Seçiniz" in results_submitted:
                        st.error("Lütfen tüm maçların sonucunu giriniz.")
                    else:
                        for i, res in enumerate(results_submitted):
                            match = st.session_state.current_pairings[i]
                            if res == "BYE":
                                match['white']['score'] += 1.0
                                continue
                                
                            w = match['white']
                            b = match['black']
                            
                            w['opponents'].append(b['name'])
                            b['opponents'].append(w['name'])
                            
                            if res == "1-0":
                                w['score'] += 1.0
                            elif res == "0-1":
                                b['score'] += 1.0
                            elif res == "0.5-0.5":
                                w['score'] += 0.5
                                b['score'] += 0.5
                        
                        standings_snapshot = copy.deepcopy(get_standings())
                        st.session_state.rounds_history.append({
                            'round': round_num,
                            'pairings': st.session_state.current_pairings,
                            'standings': standings_snapshot
                        })
                        
                        st.session_state.current_pairings = []
                        st.session_state.round_active = False
                        st.success("Tur tamamlandı!")
                        st.rerun()
            
            st.divider()
            st.caption("Anlık Sıralama Önizleme")
            st.dataframe(pd.DataFrame(get_standings())[['name', 'score']], hide_index=True)

# --- TAB 3: GEÇMİŞ ---
with tab3:
    if not st.session_state.rounds_history:
        st.info("Henüz tamamlanmış tur yok.")
    else:
        selected_round = st.selectbox("Görüntülenecek Turu Seçin", [r['round'] for r in st.session_state.rounds_history])
        round_data = st.session_state.rounds_history[selected_round - 1]
        
        st.subheader(f"{selected_round}. Tur Sonuçları")
        hist_df = pd.DataFrame(round_data['standings'])
        hist_df.index = hist_df.index + 1
        st.dataframe(hist_df[['name', 'elo', 'score', 'buc1', 'buct']], use_container_width=True)
        
        pdf_hist = create_pdf("standings", round_data['standings'], selected_round, metadata)
        st.download_button(f"📥 {selected_round}. Tur PDF İndir", data=pdf_hist, file_name=f"tur_{selected_round}_sonuc.pdf", mime="application/pdf")
