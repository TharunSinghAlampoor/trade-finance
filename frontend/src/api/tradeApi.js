import axios from 'axios';

const API = axios.create({ baseURL: 'http://localhost:8000' });

API.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

export const tradeService = {
    createTrade: (data) => API.post('/trades/', null, { 
        params: {
            buyer_email: data.buyer_email,
            seller_email: data.seller_email,
            description: data.description,
            amount: data.amount,
            currency: data.currency,
            remarks: data.remarks
        } 
    }),
    listTrades: () => API.get('/trades/'),
    getTrade: (id) => API.get(`/trades/${id}`),
    updateStatus: (id, status, remarks) => 
        API.put(`/trades/${id}/status`, null, { 
            params: { new_status: status, remarks } 
        }),
    confirmExpectedDate: (id) => API.patch(`/trades/${id}/expected-date/confirm`, {})
};

export default tradeService;