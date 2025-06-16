// // app/page.tsx

import { redirect } from 'next/navigation';

export default function Home() {
  redirect('/chat');
}

// import BotUI from '@/components/BotUI';  // Using the @ alias

// export default function HomePage() {
//   return (
//     <main>
//       <BotUI />
//     </main>
//   );
// }
