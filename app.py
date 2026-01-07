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

def create_combined_pdf(round_num, pairings_data, standings_data, metadata):
    """Hem Maç Sonuçlarını Hem Puan Tablosunu İçeren PDF"""
    pdf = FPDF()
    pdf.add_page()
    
    # --- LOGO ve BAŞLIK ---
    if os.path.exists("logo.jpg"):
        pdf.image("logo.jpg", x=10, y=8, w=25)
    
    pdf.set_y(10)
    pdf.set_font("Arial", 'B', 16)
    # Logoya çarpmaması için biraz sağdan başlatıyoruz veya ortalıyoruz
    pdf.cell(0, 10, tr_to_latin(metadata['name']), ln=True, align='C')
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, tr_to_latin(f"Tarih: {metadata['date']} | Yer: {metadata['location']}"), ln=True, align='C')
    
    # --- BÖLÜM 1: MAÇ SONUÇLARI ---
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, tr_to_latin(f"{round_num}. Tur Mac Sonuclari"), ln=True, align='L')
    
    pdf.set_font("Arial", 'B', 9)
    # Tablo Başlıkları
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(15, 6, "Masa", 1, 0, 'C', 1)
    pdf.cell(65, 6, "Beyaz", 1, 0, 'L', 1)
    pdf.cell(25, 6, "Sonuc", 1, 0, 'C', 1)
    pdf.cell(65, 6, "Siyah", 1, 1, 'L', 1)
    
    pdf.set_font("Arial", '', 9)
    for i, match in enumerate(pairings_data, 1):
        w = tr_to_latin(match['white']['name'])
        b = match['black']['name']
        
        result_text = match.get('result', '-')
        
        # Sonucu formatla
        if result_text == "1-0": result_text = "1 - 0"
        elif result_text == "0-1": result_text = "0 - 1"
        elif result_text == "0.5-0.5": result_text = "1/2 - 1/2"
        elif result_text == "BYE": 
            result_text = "BYE"
            b = "BAY (Rakipsiz)"
        
        b = tr_to_latin(b)

        pdf.cell(15, 6, str(i), 1, 0, 'C')
        pdf.cell(65, 6, w, 1, 0, 'L')
        pdf.cell(25, 6, result_text, 1, 0, 'C')
        pdf.cell(65, 6, b, 1, 1, 'L')

    # --- BÖLÜM 2: PUAN DURUMU ---
    pdf.ln(8)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, tr_to_latin(f"{round_num}. Tur Sonrasi Puan Durumu"), ln=True, align='L')
    
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(10, 6, "Sira", 1, 0, 'C', 1)
    pdf.cell(70, 6, "Isim", 1, 0, 'L', 1)
    pdf.cell(15, 6, "ELO", 1, 0, 'C', 1)
    pdf.cell(15, 6, "Puan", 1, 0, 'C', 1)
    pdf.cell(15, 6, "Buc-1", 1, 0, 'C', 1)
    pdf.cell(15, 6, "Buc-T", 1, 1, 'C', 1)
    
    pdf.set_font("Arial", '', 8)
    for i, p in enumerate(standings_data, 1):
        pdf.cell(10, 6, str(i), 1, 0, 'C')
        pdf.cell(70, 6, tr_to_latin(p['name']), 1, 0, 'L')
        pdf.cell(15, 6, str(p['elo']), 1, 0, 'C')
        pdf.cell(15, 6, str(p['score']), 1, 0, 'C')
        pdf.cell(15, 6, str(p['buc1']), 1, 0, 'C')
        pdf.cell(15, 6, str(p['buct']), 1, 1, 'C')

    # --- ALT BİLGİ & BAĞIŞ ---
    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, tr_to_latin("Kurtkoy Satranc ve Akil Oyunlari Spor Kulubu"), ln=True, align='C')
    pdf.ln(1)
    pdf.set_font("Arial", 'B', 9)
    # Bağış yazısı
    donation_text = "Kulubumuzun gelismesi ve daha iyi imkanlar sunabilmemiz icin lutfen bagista bulunun. Destekleriniz genclerimiz icin onemlidir."
    pdf.multi_cell(0, 5, tr_to_latin(donation_text), align='C')
    
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
    st.image("logo.jpg", width=120) if os.path.exists("logo.jpg") else st.write("♟️")
    st.header("Turnuva Ayarları")
    
    t_name = st.text_input("Turnuva Adı", value="Kurtköy Satranç Turnuvası")
    t_date = st.date_input("Tarih", value=datetime.today())
    t_loc = st.text_input("Konum", value="Kulüp Merkezi")
    
    # TUR SAYISI GİRİŞİ
    total_rounds = st.number_input("Toplam Tur Sayısı", min_value=1, value=5, step=1)
    
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
st.caption(f"📅 {t_date} | 📍 {t_loc} | 🏁 Toplam {total_rounds} Tur")

tab1, tab2, tab3 = st.tabs(["👥 Oyuncu Listesi & Düzenle", "⚔️ Turnuva Yönetimi", "📜 Geçmiş Turlar"])

# --- TAB 1: OYUNCU YÖNETİMİ ---
with tab1:
    if st.session_state.rounds_history:
        st.warning("Turnuva başladıktan sonra oyuncu silmek veya Elo değiştirmek teknik olarak önerilmez!")
    
    if st.session_state.players:
        df_players = pd.DataFrame(st.session_state.players)
        # Tabloda gösterim için düzenleme
        df_display = df_players[['name', 'elo', 'score']]
        st.dataframe(df_display, column_config={"name": "Ad Soyad", "elo": "ELO", "score": "Puan"}, hide_index=True, use_container_width=True)
        
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
        
        st.dataframe(pd.DataFrame(final_standings)[['name', 'elo', 'score', 'buc1', 'buct']], hide_index=True)
        
        # FİNAL PDF (Son Turun raporu aslında final raporudur ama sadece tablo istenirse burası kullanılabilir)
        # Ancak biz son tur geçmişinden almayı öneriyoruz.
        
    else:
        # Mevcut tur sayısı
        current_round_num = len(st.session_state.rounds_history) + 1
        
        if not st.session_state.round_active:
            # TUR BAŞLATMA EKRANI
            if current_round_num > total_rounds:
                st.warning(f"Belirlenen {total_rounds} tur tamamlandı!")
                if st.button("🏁 Turnuvayı Resmen Bitir ve Sonuçları Yayınla"):
                    st.session_state.tournament_finished = True
                    st.rerun()
            else:
                if st.button(f"{current_round_num}. Tur Eşleşmelerini Yap", type="primary"):
                    players = st.session_state.players
                    random.shuffle(players)
                    players.sort(key=lambda x: (x['score'], x['elo']), reverse=True)
                    
                    unpaired = players[:]
                    pairings = []
                    bye_player = None
                    
                    if len(unpaired) % 2 == 1:
                        bye_player = unpaired.pop()
                    
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

        else:
            # AKTİF TUR EKRANI (MAÇLAR OYNANIYOR)
            st.subheader(f"Masa Düzeni - {current_round_num}. Tur")
            
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
                        res = st.selectbox(f"Masa {i} Sonuç", ["Seçiniz", "1-0", "0-1", "0.5-0.5"], key=f"res_{current_round_num}_{i}", label_visibility="collapsed")
                    with c3: st.write(f"⚫ {b['name']} ({b['elo']})")
                    st.markdown("---")
                    results_submitted.append(res)
                
                if st.form_submit_button("Sonuçları Kaydet ve Turu Bitir"):
                    if "Seçiniz" in results_submitted:
                        st.error("Lütfen tüm maçların sonucunu giriniz.")
                    else:
                        # 1. Sonuçları İşle
                        for i, res in enumerate(results_submitted):
                            match = st.session_state.current_pairings[i]
                            # Sonucu pairing objesine de kaydet (PDF için lazım)
                            match['result'] = res 
                            
                            if res == "BYE":
                                match['white']['score'] += 1.0
                                continue
                                
                            w = match['white']
                            b = match['black']
                            
                            w['opponents'].append(b['name'])
                            b['opponents'].append(w['name'])
                            
                            if res == "1-0": w['score'] += 1.0
                            elif res == "0-1": b['score'] += 1.0
                            elif res == "0.5-0.5": 
                                w['score'] += 0.5
                                b['score'] += 0.5
                        
                        # 2. Puan Durumunu Güncelle ve Kaydet
                        standings_snapshot = copy.deepcopy(get_standings())
                        pairings_snapshot = copy.deepcopy(st.session_state.current_pairings)
                        
                        st.session_state.rounds_history.append({
                            'round': current_round_num,
                            'pairings': pairings_snapshot,
                            'standings': standings_snapshot
                        })
                        
                        st.session_state.current_pairings = []
                        st.session_state.round_active = False
                        st.success("Tur tamamlandı! Geçmiş Turlar sekmesinden raporu alabilirsiniz.")
                        st.rerun()
            
            st.divider()
            st.caption("Anlık Puan Durumu (Önizleme)")
            st.dataframe(pd.DataFrame(get_standings())[['name', 'score']], hide_index=True)

# --- TAB 3: GEÇMİŞ ve RAPORLAR ---
with tab3:
    if not st.session_state.rounds_history:
        st.info("Henüz tamamlanmış tur yok.")
    else:
        # Son tur varsayılan olarak seçili gelsin
        rounds_list = [r['round'] for r in st.session_state.rounds_history]
        selected_round = st.selectbox("Görüntülenecek Turu Seçin", rounds_list, index=len(rounds_list)-1)
        
        round_data = st.session_state.rounds_history[selected_round - 1]
        
        st.subheader(f"{selected_round}. Tur Raporu")
        
        # PDF OLUŞTURMA (Maçlar + Puan Durumu)
        pdf_bytes = create_combined_pdf(selected_round, round_data['pairings'], round_data['standings'], metadata)
        
        col_dl, col_view = st.columns([1, 2])
        with col_dl:
            st.download_button(
                label=f"📥 {selected_round}. Tur Tam Rapor İndir (PDF)",
                data=pdf_bytes,
                file_name=f"Turnuva_Raporu_Tur_{selected_round}.pdf",
                mime="application/pdf",
                type="primary"
            )
        
        st.write("---")
        st.write("**Bu Turun Puan Durumu:**")
        hist_df = pd.DataFrame(round_data['standings'])
        hist_df.index = hist_df.index + 1
        st.dataframe(hist_df[['name', 'elo', 'score', 'buc1', 'buct']], use_container_width=True)
