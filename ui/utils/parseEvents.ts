/**
 * Parse structured events from AI response content.
 *
 * Looks for ---EVENT--- / ---END-EVENT--- blocks and extracts
 * title, date, time, location, description, and originalLink fields.
 *
 * Requires title, date, and time to all be present for an event to be included.
 */

export interface ParsedEvent {
  title: string;
  date: string;
  time: string;
  location: string;
  description: string;
  originalLink?: string;
}

export function parseEventsFromContent(content: string): ParsedEvent[] {
  const events: ParsedEvent[] = [];

  // Support both singular EVENT and plural EVENTS
  const eventBlockRegex = /---EVENTS?---([\s\S]*?)---END-EVENTS?---/g;
  let blockMatch;

  while ((blockMatch = eventBlockRegex.exec(content)) !== null) {
    const eventsBlock = blockMatch[1];

    // Split individual events by looking for title: patterns
    const eventEntries = eventsBlock
      .split(/(?=title:)/g)
      .filter((entry) => entry.trim());

    eventEntries.forEach((eventData) => {
      const extractField = (data: string, field: string): string => {
        const regex = new RegExp(`${field}:\\s*(.*)`, 'i');
        const match = data.match(regex);
        return match ? match[1].trim() : '';
      };

      const event: ParsedEvent = {
        title: extractField(eventData, 'title'),
        date: extractField(eventData, 'date'),
        time: extractField(eventData, 'time'),
        location: extractField(eventData, 'location'),
        description: extractField(eventData, 'description'),
        originalLink: extractField(eventData, 'originalLink'),
      };

      if (event.title && event.date && event.time) {
        events.push(event);
      }
    });
  }

  return events;
}

/**
 * Remove event blocks from content so they don't render as raw text.
 */
export function stripEventBlocks(content: string): string {
  return content.replace(/---EVENTS?---[\s\S]*?---END-EVENTS?---/g, '');
}
