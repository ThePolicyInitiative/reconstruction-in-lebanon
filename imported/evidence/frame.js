/* Fit an embedded archive below the host tab bar, keeping its own scroll area. */
(() => {
  let lastHeight = 0, pending = false, forceNext = false;
  const send = (type, extra = {}) => window.parent.postMessage({isStreamlitMessage:true, type, ...extra}, '*');
  const resize = force => {
    let height = window.innerHeight;
    try {
      const frame = window.frameElement;
      if (frame) {
        const viewport = window.parent.visualViewport;
        const bottom = viewport ? viewport.offsetTop + viewport.height : window.parent.innerHeight;
        height = Math.floor(bottom - frame.getBoundingClientRect().top);
      }
    } catch { /* Keep the current viewport height if the host is cross-origin. */ }
    height = Math.max(160, height);
    if (force || height !== lastHeight) {
      lastHeight = height;
      send('streamlit:setFrameHeight', {height});
    }
  };
  const schedule = (force = false) => {
    forceNext ||= force;
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => {
      pending = false;
      const force = forceNext;
      forceNext = false;
      resize(force);
    });
  };
  const onLayout = () => schedule();
  addEventListener('message', event => {
    if (event.source === window.parent && event.data?.type === 'streamlit:render') schedule(true);
  });
  const observer = new ResizeObserver(onLayout);
  observer.observe(document.body);
  let host, viewport;
  try {
    host = window.parent;
    viewport = host.visualViewport;
    host.addEventListener('resize', onLayout);
    host.addEventListener('scroll', onLayout, true);
    viewport?.addEventListener('resize', onLayout);
    viewport?.addEventListener('scroll', onLayout);
    const frame = window.frameElement;
    if (frame) {
      observer.observe(frame);
      const header = host.document.querySelector('.st-key-site-header');
      if (header) observer.observe(header);
    }
  } catch { /* Parent measurements are optional outside the Streamlit host. */ }
  addEventListener('load', () => schedule(true));
  addEventListener('resize', onLayout);
  addEventListener('pageshow', () => schedule(true));
  addEventListener('pagehide', () => {
    observer.disconnect();
    host?.removeEventListener('resize', onLayout);
    host?.removeEventListener('scroll', onLayout, true);
    viewport?.removeEventListener('resize', onLayout);
    viewport?.removeEventListener('scroll', onLayout);
  }, {once:true});
  send('streamlit:componentReady', {apiVersion:1});
  schedule(true);
})();
