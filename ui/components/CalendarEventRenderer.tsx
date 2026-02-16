import React, { useState, useEffect } from 'react';
import { CalendarButton } from './CalendarButton';
import type { CalendarEvent } from './CalendarButton';

export interface CalendarEventRendererProps {
  events: CalendarEvent[];
  apiBase: string;
  organizationName?: string;
  curatedByText?: string;
  onAddToCalendar?: (success: boolean, message: string) => void;
}

export const CalendarEventRenderer: React.FC<CalendarEventRendererProps> = ({
  events,
  apiBase,
  organizationName = 'DeSilo',
  curatedByText,
  onAddToCalendar,
}) => {
  const [email, setEmail] = useState('');
  const [isValid, setIsValid] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [showBulkEmailInput, setShowBulkEmailInput] = useState(false);

  if (events.length === 0) return null;

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

  const byText = curatedByText || `Curated by ${organizationName} AI Assistant`;

  const handleAddAllToCalendar = async () => {
    if (!isValid || isAdding || events.length === 0) return;
    setIsAdding(true);

    try {
      const apiUrl = `${apiBase}/api/notifications/calendar-invite`;

      const results = await Promise.allSettled(
        events.map((event) =>
          fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email: email,
              event: {
                title: `[${organizationName}] ${event.title}`,
                date: formatDateTime(event.date, event.time),
                location: event.location,
                description: `${byText}\n\n${event.description}\n\n${event.originalLink ? `View original event: ${event.originalLink}` : ''}`,
                url: event.originalLink || '',
              },
            }),
          })
        )
      );

      const succeeded = results.filter((r) => r.status === 'fulfilled').length;
      if (succeeded > 0) {
        onAddToCalendar?.(
          true,
          `${succeeded} calendar invite${succeeded > 1 ? 's' : ''} sent to ${email}!`
        );
        setShowBulkEmailInput(false);
      } else {
        throw new Error('Failed to add events to calendar');
      }
    } catch (error) {
      console.error('Bulk calendar error:', error);
      onAddToCalendar?.(
        false,
        'Failed to add events to calendar. Please try again.'
      );
    } finally {
      setIsAdding(false);
    }
  };

  // Single event
  if (events.length === 1) {
    return (
      <div style={{ marginTop: '16px' }}>
        <h4
          style={{
            fontSize: '1.1rem',
            fontWeight: 700,
            marginBottom: '12px',
            color: '#0a0a0a',
          }}
        >
          📅 Upcoming Event - Add to Your Calendar
        </h4>
        <CalendarButton
          event={events[0]}
          apiBase={apiBase}
          organizationName={organizationName}
          curatedByText={curatedByText}
          onAddToCalendar={onAddToCalendar}
        />
      </div>
    );
  }

  // Multiple events
  return (
    <div style={{ marginTop: '16px' }}>
      <h4
        style={{
          fontSize: '1.1rem',
          fontWeight: 700,
          marginBottom: '12px',
          color: '#0a0a0a',
        }}
      >
        📅 Upcoming Events - Add to Your Calendar
      </h4>

      {events.map((event, index) => (
        <CalendarButton
          key={index}
          event={event}
          apiBase={apiBase}
          organizationName={organizationName}
          curatedByText={curatedByText}
          onAddToCalendar={onAddToCalendar}
        />
      ))}

      {/* Bulk Add All Option */}
      <div
        style={{
          marginTop: '20px',
          padding: '16px',
          background: 'rgba(230, 126, 34, 0.1)',
          border: '3px solid #e67e22',
          borderRadius: '4px',
          boxShadow: '5px 5px 0px rgba(230, 126, 34, 0.3)',
        }}
      >
        <div
          style={{
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <span style={{ fontSize: '1.2rem' }}>⚡</span>
          <h5
            style={{
              margin: 0,
              fontSize: '1rem',
              fontWeight: 700,
              color: '#e67e22',
              textTransform: 'uppercase',
              letterSpacing: '-0.02em',
            }}
          >
            Quick Add All {events.length} Events
          </h5>
        </div>

        {!showBulkEmailInput ? (
          <button
            onClick={() => setShowBulkEmailInput(true)}
            style={{
              width: '100%',
              padding: '12px 16px',
              background:
                'linear-gradient(135deg, #e67e22 0%, #f39c12 100%)',
              color: '#ffffff',
              border: '2px solid #0a0a0a',
              borderRadius: '4px',
              fontSize: '0.95rem',
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
            📅 Add All {events.length} Events to Calendar
          </button>
        ) : (
          <div
            style={{
              display: 'flex',
              gap: '8px',
              alignItems: 'center',
            }}
          >
            <input
              type="email"
              value={email}
              onChange={handleEmailChange}
              placeholder="your@email.com"
              style={{
                padding: '10px 12px',
                border: '2px solid #0a0a0a',
                borderRadius: '4px',
                fontSize: '0.9rem',
                background: 'white',
                flex: 1,
                minWidth: '200px',
              }}
            />
            <button
              onClick={handleAddAllToCalendar}
              disabled={!isValid || isAdding}
              style={{
                padding: '10px 16px',
                background: isValid ? '#28a745' : '#cccccc',
                color: isValid ? '#ffffff' : '#666666',
                border: 'none',
                borderRadius: '4px',
                fontSize: '0.9rem',
                fontWeight: 700,
                cursor: isValid ? 'pointer' : 'not-allowed',
              }}
            >
              {isAdding ? '📤 Adding...' : `✓ Add ${events.length}`}
            </button>
            <button
              onClick={() => setShowBulkEmailInput(false)}
              style={{
                padding: '10px 12px',
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
    </div>
  );
};
