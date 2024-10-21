// frontend/src/components/QueryCard.jsx
import React from 'react';
import './QueryCard.css';

const QueryCard = ({ query }) => {
    const { id, short_description, created_at, status, progress } = query;

    const getStatusColor = (status) => {
        switch(status) {
            case 'В обработке':
                return 'orange';
            case 'Декомпозирован':
                return 'blue';
            case 'Завершен':
                return 'green';
            default:
                return 'grey';
        }
    };

    return (
        <div className="query-card">
            <h3>{short_description}</h3>
            <p>Дата создания: {new Date(created_at).toLocaleDateString()}</p>
            <p>Статус: <span style={{color: getStatusColor(status)}}>{status}</span></p>
            <div className="progress-bar">
                <div className="progress" style={{ width: `${progress}%` }}></div>
            </div>
            <button className="details-button">Подробнее</button>
        </div>
    );
};

export default QueryCard;