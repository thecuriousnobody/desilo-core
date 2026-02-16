import React, { useState, useEffect } from 'react';

export interface CalendarEvent {
  title: string;
  date: string;
  time: string;
  location: string;
  description: string;
  originalLink?: string;
}

export interface CalendarButtonProps {
  event: CalendarEvent;
  apiBase: string;
  organizationName?: string;
  curatedByText?: string;
  onAddToCalendar?: (success: boolean, message: string) => void;
}

export const CalendarButton: React.FC<CalendarButtonProps> = ({
  event,
  apiBase,
  organizationName = 'DeSilo',
  curatedByText,
  onAddToCalendar,
}) => {
  const [email, setEmail] = useState('');
  const [isValid, setIsValid] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [showEmailInput, setShowEmailInput] = useState(false);

  useEffect(() => {
    const savedEmail = localStorage.getItem('calendarEmail');
    if (savedEmail) {
      setEmail(savedEmail);
      setIsValid(validateEmail(savedEmail));
    }
  }, []);

  const validateEmail = (value: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmail(value);
    setIsValid(validateEmail(value));
    if (validateEmail(value)) {
      localStorage.setItem('calendarEmail', value);
    }
  };

  const parseDate = (dateStr: string) => {
    try {
      let date: Date;
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        const [year, month, day] = dateStr.split('-');
        date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      } else if (/^[A-Za-z]+ \d{1,2}, \d{4}$/.test(dateStr)) {
        date = new Date(dateStr);
      } else if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(dateStr)) {
        date = new Date(dateStr);
      } else {
        date = new Date(dateStr);
      }
      if (isNaN(date.getTime())) throw new Error('Invalid date');
      return date;
    } catch {
      return new Date();
    }
  };

  const formatDisplayDate = (dateStr: string) => {
    try {
      const date = parseDate(dateStr);
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const formatDisplayTime = (timeStr: string) => {
    try {
      if (/^\d{1,2}:\d{2}\s*(AM|PM)$/i.test(timeStr)) return timeStr;
      if (/^\d{1,2}:\d{2}$/.test(timeStr)) {
        const [hours, minutes] = timeStr.split(':');
        const hour24 = parseInt(hours);
        const hour12 = hour24 === 0 ? 12 : hour24 > 12 ? hour24 - 12 : hour24;
        const ampm = hour24 < 12 ? 'AM' : 'PM';
        return `${hour12}:${minutes} ${ampm}`;
      }
      return timeStr;
    } catch {
      return timeStr;
    }
  };

  const formatDateTime = (date: string, time: string) => {
    try {
      const parsedDate = parseDate(date);
      const year = parsedDate.getFullYear();
      const month = String(parsedDate.getMonth() + 1).padStart(2, '0');
      const day = String(parsedDate.getDate()).padStart(2, '0');

      const normalizedTime = formatDisplayTime(time);
      const timeMatch = normalizedTime.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);
      if (!timeMatch) return `${year}-${month}-${day}T12:00:00-06:00`;

      let hours = parseInt(timeMatch[1]);
      const minutes = timeMatch[2];
      const ampm = timeMatch[3].toUpperCase();

      if (ampm === 'PM' && hours !== 12) hours += 12;
      if (ampm === 'AM' && hours === 12) hours = 0;

      return `${year}-${month}-${day}T${hours.toString().padStart(2, '0')}:${minutes}:00-06:00`;
    } catch {
      return `${new Date().toISOString().split('T')[0]}T12:00:00-06:00`;
    }
  };

  const handleAddToCalendar = async () => {
    if (!isValid || isAdding) return;
    setIsAdding(true);

    const byText =
      curatedByText || `Curated by ${organizationName} AI Assistant`;

    try {
      const payload = {
        email: email,
        event: {
          title: `[${organizationName}] ${event.title}`,
          date: formatDateTime(event.date, event.time),
          location: event.location,
          description: `${byText}\n\n${event.description}\n\n${event.originalLink ? `View original event: ${event.originalLink}` : ''}`,
          url: event.originalLink || '',
        },
      };

      const response = await fetch(
        `${apiBase}/api/notifications/calendar-invite`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }
      );

      if (response.ok) {
        onAddToCalendar?.(true, `Calendar invite sent to ${email}!`);
        setShowEmailInput(false);
      } else {
        throw new Error('Failed to add to calendar');
      }
    } catch (error) {
      console.error('Calendar error:', error);
      onAddToCalendar?.(
        false,
        'Failed to add to calendar. Please try again.'
      );
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div
      style={{
        marginTop: '12px',
        padding: '12px',
        background: 'rgba(248, 246, 240, 0.9)',
        border: '2px solid #0a0a0a',
        borderRadius: '4px',
      }}
    >
      <div style={{ marginBottom: '12px' }}>
        <div
          style={{
            fontSize: '1.1rem',
            fontWeight: 700,
            color: '#0a0a0a',
            marginBottom: '8px',
            lineHeight: '1.2',
          }}
        >
          {event.title}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.9rem',
            fontWeight: 600,
            color: '#666',
            marginBottom: '8px',
          }}
        >
          <span>📅</span>
          <span>
            {formatDisplayDate(event.date)} at{' '}
            {formatDisplayTime(event.time)}
          </span>
          <span>•</span>
          <span>📍 {event.location}</span>
        </div>

        {event.originalLink && (
          <div style={{ marginBottom: '12px' }}>
            <a
              href={event.originalLink}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-block',
                padding: '6px 12px',
                background: 'rgba(74, 144, 226, 0.1)',
                color: '#4a90e2',
                border: '1px solid #4a90e2',
                borderRadius: '3px',
                fontSize: '0.85rem',
                fontWeight: 600,
                textDecoration: 'none',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                transition: 'all 0.2s ease',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = '#4a90e2';
                e.currentTarget.style.color = '#ffffff';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background =
                  'rgba(74, 144, 226, 0.1)';
                e.currentTarget.style.color = '#4a90e2';
              }}
            >
              🔗 Link to Event
            </a>
          </div>
        )}
      </div>

      {!showEmailInput ? (
        <button
          onClick={() => setShowEmailInput(true)}
          style={{
            padding: '8px 16px',
            background:
              'linear-gradient(135deg, #e67e22 0%, #f39c12 100%)',
            color: '#ffffff',
            border: '2px solid #0a0a0a',
            borderRadius: '4px',
            fontSize: '0.9rem',
            fontWeight: 700,
            cursor: 'pointer',
            textTransform: 'uppercase',
            letterSpacing: '-0.02em',
            boxShadow: '3px 3px 0px rgba(0, 0, 0, 0.8)',
            transition: 'all 0.2s ease',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow =
              '5px 5px 0px rgba(0, 0, 0, 0.8)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow =
              '3px 3px 0px rgba(0, 0, 0, 0.8)';
          }}
        >
          📅 Add to Calendar
        </button>
      ) : (
        <div
          style={{ display: 'flex', gap: '8px', alignItems: 'center' }}
        >
          <input
            type="email"
            value={email}
            onChange={handleEmailChange}
            placeholder="your@email.com"
            style={{
              padding: '8px 12px',
              border: '2px solid #0a0a0a',
              borderRadius: '4px',
              fontSize: '0.9rem',
              background: 'white',
              flex: 1,
              minWidth: '200px',
            }}
          />
          <button
            onClick={handleAddToCalendar}
            disabled={!isValid || isAdding}
            style={{
              padding: '8px 16px',
              background: isValid ? '#28a745' : '#cccccc',
              color: isValid ? '#ffffff' : '#666666',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.9rem',
              fontWeight: 700,
              cursor: isValid ? 'pointer' : 'not-allowed',
            }}
          >
            {isAdding ? '📤 Adding...' : '✓ Add'}
          </button>
          <button
            onClick={() => setShowEmailInput(false)}
            style={{
              padding: '8px 12px',
              background: '#dc3545',
              color: '#ffffff',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.9rem',
              cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
};
