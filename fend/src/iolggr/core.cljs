(ns iolggr.core
  (:require
    [cljsjs.material-ui]
    [cljs-react-material-ui.core :as ui]
    [cljs-react-material-ui.icons :as ic]
    [goog.dom :as gdom]
    [vega-tools.core :as vega-tools]
    [promesa.core :as p]
    [cljs.core.async :as async :refer [<! >! put! chan]]
    [clojure.string :as string]
    [om.next :as om :refer-macros [defui]]
    [om.dom :as dom])
  (:require-macros [cljs.core.async.macros :refer [go]])
  (:import [goog Uri]
           [goog.net Jsonp]))

(def initial-spec
  {:width   640
   :height  480
   :padding {:top 10, :left 30, :bottom 30, :right 10}

   :data
            [{:name   "table"
              :values [{:x 1, :y 28} {:x 2, :y 55}
                       {:x 3, :y 43} {:x 4, :y 91}
                       {:x 5, :y 81} {:x 6, :y 53}
                       {:x 7, :y 19} {:x 8, :y 87}
                       {:x 9, :y 52} {:x 10, :y 48}
                       {:x 11, :y 24} {:x 12, :y 49}
                       {:x 13, :y 87} {:x 14, :y 66}
                       {:x 15, :y 17} {:x 16, :y 27}
                       {:x 17, :y 68} {:x 18, :y 16}
                       {:x 19, :y 49} {:x 20, :y 15}]}]

   :scales
            [{:name   "x"
              :type   "ordinal"
              :range  "width"
              :domain {:data "table", :field "x"}}
             {:name   "y"
              :type   "linear"
              :range  "height"
              :domain {:data "table", :field "y"}, :nice true}]

   :axes
            [{:type "x", :scale "x"}
             {:type "y", :scale "y"}]

   :marks
            [{:type       "rect", :from {:data "table"},
              :properties {:enter  {:x     {:scale "x", :field "x"}
                                    :width {:scale "x", :band true, :offset -1}
                                    :y     {:scale "y", :field "y"}
                                    :y2    {:scale "y", :value 0}}
                           :update {:fill {:value "steelblue"}}
                           :hover  {:fill {:value "red"}}}}]})

(defui Chart
  Object
  (render [this]
    (dom/div nil "chart"))
  (componentDidMount [this]
    (-> (vega-tools/validate-and-parse initial-spec)
        (p/catch #(js/alert (str "Unable to parse spec:\n\n" %)))
        (p/then #(-> (% {:el (dom/node this)})
                     (.update))))))

(enable-console-print!)

(def init-data
  {:list/one [{:name "John" :points 0}
              {:name "Mary" :points 0}
              {:name "Bob" :points 0}]
   :list/two [{:name "Mary" :points 0 :age 27}
              {:name "Gwen" :points 0}
              {:name "Jeff" :points 0}]})

;; -----------------------------------------------------------------------------
;; Parsing

;         name dispatch-fn
(defmulti read om/dispatch)

(defn get-people [state key]
  (let [st @state]
    (into [] (map #(get-in st %)) (get st key))))

; read function must return a hashmap containing a :value entry
(defmethod read :list/one
  ; the signature of a read fn is [env key params] - env is a hash map containing context & key is the requested key
  ; destructuring state from env
  [{:keys [state] :as env} key params]
  {:value (get-people state key)})

(defmethod read :list/two
  [{:keys [state] :as env} key params]
  {:value (get-people state key)})

(defmulti mutate om/dispatch)

; mutations return :action (function with no arguments)
; :value is the a hashmap with :keys communicates what read operations should follow a mutation
(defmethod mutate 'points/increment
  [{:keys [state]} _ {:keys [name]}]
  {:action
   (fn []
     (swap! state update-in
            [:person/by-name name :points]
            inc))})

(defmethod mutate 'points/decrement
  [{:keys [state]} _ {:keys [name]}]
  {:action
   (fn []
     (swap! state update-in
            [:person/by-name name :points]
            #(let [n (dec %)] (if (neg? n) 0 n))))})

;; -----------------------------------------------------------------------------
;; Components

(ui/mui-theme-provider
  {:mui-theme (ui/get-mui-theme (aget js/MaterialUIStyles "DarkRawTheme"))}
  (ui/paper "Hello dark world"))

(defui Person
  static om/Ident
  (ident [this {:keys [name]}]
    [:person/by-name name])
  static om/IQuery
  (query [this]
    '[:name :points :age])
  Object
  (render [this]
    (let [{:keys [points name] :as props} (om/props this)]
      (ui/list-item
        (dom/label nil (str name ", points: " points))
        (dom/button
          #js {:onClick
               (fn [e]
                 (om/transact! this
                               `[(points/increment ~props)]))}
          "+")
        (dom/button
          #js {:onClick
               (fn [e]
                 (om/transact! this
                               `[(points/decrement ~props)]))}
          "-")))

    )
  )

(def person (om/factory Person {:keyfn :name}))

(defui ListView
  Object
  (render [this]
    (let [list (om/props this)]
      (apply ui/list
             (map person list)))))

(def list-view (om/factory ListView))

(defui RootView
  static om/IQuery
  (query [this]
    (let [subquery (om/get-query Person)]
      `[{:list/one ~subquery} {:list/two ~subquery}]))
  Object
  (render [this]
    (let [{:keys [list/one list/two]} (om/props this)]
      (ui/mui-theme-provider
        {:mui-theme (ui/get-mui-theme)}
        (dom/div
          #js {:className "h-100"}
          (ui/app-bar
            {:title "iolggr"})
          (ui/paper
                            (list-view one)
                          (list-view two)
                 )
          )
        )
      )
    ))

(def reconciler
  (om/reconciler
    {:state  init-data
     :parser (om/parser {:read read :mutate mutate})}))

(om/add-root! reconciler
              RootView (gdom/getElement "app"))

