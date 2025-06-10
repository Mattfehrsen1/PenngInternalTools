import { cn } from '@/lib/utils';
import { Bot, User } from 'lucide-react';
import { Citation } from '@/lib/api';
import ReactMarkdown from 'react-markdown';

interface MessageProps {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

export function Message({ role, content, citations }: MessageProps) {
  return (
    <div className={cn(
      'flex gap-4 p-4 rounded-lg',
      role === 'assistant' ? 'bg-muted/50' : ''
    )}>
      <div className="flex-shrink-0">
        {role === 'assistant' ? (
          <Bot className="h-6 w-6 text-muted-foreground" />
        ) : (
          <User className="h-6 w-6 text-muted-foreground" />
        )}
      </div>
      <div className="flex-1 space-y-2">
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
        {citations && citations.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Sources:</p>
            <div className="space-y-2">
              {citations.map((citation) => (
                <div
                  key={citation.id}
                  className="text-sm p-3 bg-muted rounded-md"
                >
                  <p className="text-xs text-muted-foreground mb-1">
                    {citation.source} (relevance: {(citation.score * 100).toFixed(0)}%)
                  </p>
                  <p className="text-sm">{citation.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
